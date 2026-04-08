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

    def add_task(self, task: str):
        self.task_queue.append(task)
        logger.info(f"Task added: {task[:80]}...")

    def perceive(self, task: str) -> str:
        self.memory.working.set_task(task)
        return f"Task received: {task}"

    def think(self, perception: str) -> str:
        allowed, reason = self.governor.can_make_request()
        if not allowed:
            logger.warning(f"Governor blocked request: {reason}")
            return f"Cannot process: {reason}"

        task_lower = perception.lower()

        needs_web = any(
            x in task_lower
            for x in [
                "score",
                "match",
                "ipl",
                "cricket",
                "football",
                "news",
                "weather",
                "stock",
                "price",
                "today",
                "current",
            ]
        )

        if "weather" in task_lower:
            for word in task_lower.split():
                if len(word) > 3:
                    try:
                        result = self.tools.call("get_weather", city=word.title())
                        if result.get("success"):
                            return f"The weather in {result['city']}: {result['temp']}°C, {result['condition']}"
                    except:
                        pass

        if (
            "wikipedia" in task_lower
            or "who is" in task_lower
            or "what is" in task_lower
        ):
            query = (
                task_lower.replace("wikipedia", "")
                .replace("who is", "")
                .replace("what is", "")
                .strip()
            )
            if query:
                try:
                    result = self.tools.call("wikipedia", query=query)
                    if result.get("success"):
                        return result["result"][:300] + "..."
                except:
                    pass

        if "news" in task_lower:
            category = "general"
            for cat in ["sports", "technology", "business", "science", "entertainment"]:
                if cat in task_lower:
                    category = cat
                    break
            try:
                result = self.tools.call("news", category=category)
                if result.get("success") and result.get("articles"):
                    articles = result["articles"]
                    headlines = "\n".join([f"• {a['title']}" for a in articles[:3]])
                    return f"Here are the latest {category} headlines:\n{headlines}"
            except:
                pass

        if needs_web and (
            "search" in task_lower or "find" in task_lower or "what" in task_lower
        ):
            query = (
                perception.replace("search", "")
                .replace("find", "")
                .replace("what is", "")
                .replace("what was", "")
                .strip()
            )
            if query:
                try:
                    result = self.tools.call("web_search", query=query, num_results=3)
                    if result.get("success") and result.get("results"):
                        info = result["results"][0]
                        return (
                            f"{info.get('title', '')}: {info.get('snippet', '')[:200]}"
                        )
                except:
                    pass

        prompt = f"""User: {perception}

Response rules:
1. Be SHORT (1 sentence)
2. Don't say "I am AURA" unless asked
3. If live data needed, say "I don't have access to live data"
4. Be natural

Response:"""
        response = self.router.think(prompt)
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
