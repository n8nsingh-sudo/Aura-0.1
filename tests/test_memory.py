import pytest
from aura.memory.fabric import MemoryFabric


class TestMemoryFabric:
    def test_initialization(self):
        fabric = MemoryFabric()
        assert fabric.working is not None
        assert fabric.episodic is not None
        assert fabric.semantic is not None
        assert fabric.longterm is not None

    def test_working_memory(self):
        fabric = MemoryFabric()
        fabric.remember("test item", memory_type="working")
        context = fabric.working.get_context_string()
        assert "test item" in context

    def test_episodic_memory(self):
        fabric = MemoryFabric()
        fabric.remember(
            "test task",
            memory_type="episode",
            task="test task",
            result="done",
            success=True,
            duration=1.0,
        )
        results = fabric.recall("test", memory_types=["episodic"])
        assert "episodic" in results

    def test_semantic_memory(self):
        fabric = MemoryFabric()
        fabric.remember(
            "Python is a programming language",
            memory_type="knowledge",
            topic="python",
            source="test",
        )
        results = fabric.recall("python", memory_types=["semantic"])
        assert "semantic" in results

    def test_get_stats(self):
        fabric = MemoryFabric()
        stats = fabric.get_stats()
        assert "working_memory_items" in stats
        assert "total_knowledge" in stats
        assert "tasks_completed" in stats
        assert "success_rate" in stats
