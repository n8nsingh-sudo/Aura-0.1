from aura.memory.working import WorkingMemory
from aura.memory.episodic import EpisodicMemory
from aura.memory.semantic import SemanticMemory
from aura.memory.longterm import LongTermMemory


class MemoryFabric:
    def __init__(self):
        self.working = WorkingMemory()
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.longterm = LongTermMemory()
        print("Memory fabric initialized — all 4 layers ready")

    def remember(self, content: str, memory_type: str = "working", **kwargs):
        if memory_type == "working":
            self.working.add(content)
        elif memory_type == "episode":
            self.episodic.record(
                task=kwargs.get("task", content),
                result=kwargs.get("result", ""),
                success=kwargs.get("success", True),
                duration=kwargs.get("duration", 0.0),
            )
        elif memory_type == "knowledge":
            self.semantic.store(
                topic=kwargs.get("topic", "general"),
                content=content,
                source=kwargs.get("source", "unknown"),
            )
        elif memory_type == "permanent":
            self.longterm.store(
                key=kwargs.get("key", content[:50]),
                value=content,
                category=kwargs.get("category", "general"),
            )

    def recall(self, query: str, memory_types: list = None) -> dict:
        if memory_types is None:
            memory_types = ["working", "episodic", "semantic"]

        results = {}

        if "working" in memory_types:
            results["working"] = self.working.get_context_string()

        if "episodic" in memory_types:
            results["episodic"] = self.episodic.search(query)

        if "semantic" in memory_types:
            results["semantic"] = self.semantic.search(query)

        return results

    def prune(self) -> dict:
        expired_longterm = self.longterm.prune_expired()
        return {"longterm_pruned": expired_longterm}

    def get_stats(self) -> dict:
        return {
            "working_memory_items": len(self.working.items),
            "total_knowledge": self.semantic.get_total_knowledge_count(),
            "tasks_completed": self.episodic.get_task_count(),
            "success_rate": self.episodic.get_success_rate() * 100,
        }
