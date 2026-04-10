import time
import logging
from aura.core.model_router import ModelRouter, ModelTier
from aura.core.governor import Governor
from aura.memory.fabric import MemoryFabric
from aura.action.tool_registry import ToolRegistry
from aura import config

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger("AURA.loop")


class AURALoop:
    def __init__(self, memory: MemoryFabric = None):
        self.router = ModelRouter()
        self.governor = Governor()
        self.memory = memory or MemoryFabric()
        self.tools = ToolRegistry()
        self.running = False
        self.current_task = None
        self.task_queue = []
        self.history = []  # Added for context memory
        self.max_history = 10  # Store up to 5 turns (user + assistant)

    def add_task(self, task: str):
        self.task_queue.append(task)
        logger.info(f"Task added: {task[:80]}...")

    def perceive(self, task: str) -> str:
        self.memory.working.set_task(task)
        return task

    def think(self, perception: str) -> str:
        allowed, reason = self.governor.can_make_request()
        if not allowed:
            logger.warning(f"Governor blocked request: {reason}")
            return f"Cannot process: {reason}"

        task_lower = perception.lower()

        needs_web = any(
            x in task_lower
            for x in [
                "who is",
                "what is",
                "tell me",
                "explain",
                "about",
                "score",
                "match",
                "ipl",
                "news",
                "weather",
                "price",
                "stock",
                "today",
                "current",
                "latest",
                "find",
                "search",
            ]
        )

        # BRD Generation Detection
        if any(
            x in task_lower
            for x in [
                "brd",
                "business requirement",
                "generate brd",
                "create brd",
                "requirements document",
            ]
        ):
            from aura.action.brd_generator import generate_brd

            brd_prompt = generate_brd(perception)
            logger.info("Generating BRD...")
            response = self.router.think(brd_prompt)
            self.governor.record_request()
            self.memory.remember(response, memory_type="working", item_type="thought")
            return response

        # [NEW: Knowledge Retrieval Phase]
        collected_knowledge = ""

        # 1. Weather Logic
        if "weather" in task_lower:
            for word in task_lower.split():
                if len(word) > 3:
                    try:
                        result = self.tools.call("get_weather", city=word.title())
                        if result.get("success"):
                            collected_knowledge += f"\n- WEATHER IN {result['city']}: {result['temp']}°C, {result['condition']}, humidity {result['humidity']}"
                    except:
                        pass

        # 2. Broad Web Search (Primary Data Source)
        if needs_web:
            try:
                # Prioritize web search for everything to get broader data
                search_query = perception
                result = self.tools.call(
                    "web_search", query=search_query, num_results=5
                )
                if result.get("success") and result.get("results"):
                    snippets = "\n".join(
                        [f"- {r['title']}: {r['snippet']}" for r in result["results"]]
                    )
                    collected_knowledge += (
                        f"\n- WEB SEARCH RESULTS (GOOGLE-STYLE):\n{snippets}"
                    )
            except:
                pass

        # 3. Wikipedia Logic (Supplemental)
        if "wikipedia" in task_lower:
            query = perception.replace("wikipedia", "").strip()
            if query:
                try:
                    result = self.tools.call("wikipedia", query=query)
                    if result.get("success"):
                        collected_knowledge += (
                            f"\n- WIKIPEDIA DETAIL: {result['result']}"
                        )
                except:
                    pass

        # 4. News Logic
        if "news" in task_lower and not collected_knowledge:
            try:
                result = self.tools.call("news")
                if result.get("success") and result.get("articles"):
                    news_text = " ".join([a["title"] for a in result["articles"][:3]])
                    collected_knowledge += f"\n- LATEST NEWS: {news_text}"
            except:
                pass

        # Formatting History and Knowledge for LLM
        history_str = ""
        if self.history:
            history_str = "\n".join(
                [
                    f"{m['role']}: {m['content']}"
                    for m in self.history[-self.max_history :]
                ]
            )
            history_str += "\n"

        knowledge_block = ""
        if collected_knowledge:
            knowledge_block = (
                f"\n[REAL-TIME KNOWLEDGE FETCHED]\n{collected_knowledge}\n"
            )

        prompt = f"""System: You are AURA (Autonomous Universal Reasoning Agent). You are NOT Qwen, Claude, OpenAI, or any other base model. You were created by Shashivendra Singh (the User) and are running locally as a personal AI assistant. Act intelligently, boldly, and exclusively as AURA.

Response rules:
1. ONLY identify as AURA.
2. Default Behavior: Be SHORT, natural, and concise (1-2 sentences).
3. "Knowledge Rule": Use the provided [REAL-TIME KNOWLEDGE] to answer current questions (scores, news, weather). If information is found, do NOT say you don't have access.
4. "Detail" Mode: If the User asks for "detail", "explanation", "long", or "elaborate", provide a deep, structured, and comprehensive response. Ignore rule #2 for such requests.
5. History Awareness: Use the provided context to answer questions referring to previous topics.
6. If asked who made you, say "I was created by Shashivendra Singh."
7. If asked who you are, say "I am AURA, your autonomous AI assistant."

{knowledge_block}
{history_str}User: {perception}
Response:"""
        response = self.router.think(prompt)

        # Update History
        self.history.append({"role": "User", "content": perception})
        self.history.append({"role": "Assistant", "content": response})
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history :]

        self.governor.record_request()

        self.memory.remember(response, memory_type="working", item_type="thought")
        return response

    def act(self, thought: str) -> str:
        logger.info(f"Acting on thought: {thought[:100]}...")
        return thought

    def observe(self, action_result: str) -> str:
        self.memory.remember(
            content=action_result,
            memory_type="episode",
            task=self.current_task or "",
            result=action_result,
            success=True,
        )
        return f"Result: {action_result}"

    def run_once(self, task: str) -> str:
        logger.info(f"Starting task: {task[:80]}")
        self.current_task = task

        start_time = time.time()
        perception = self.perceive(task)
        thought = self.think(perception)

        logger.info(f"Task complete: {thought[:80]}")

        return thought

    def run_forever(self):
        self.running = True
        logger.info("AURA is running...")

        while self.running:
            if self.task_queue:
                task = self.task_queue.pop(0)
                self.current_task = task
                try:
                    result = self.run_once(task)
                except Exception as e:
                    logger.error(f"Error processing task: {e}")
            else:
                time.sleep(1)

    def stop(self):
        self.running = False
        logger.info("AURA stopped")
