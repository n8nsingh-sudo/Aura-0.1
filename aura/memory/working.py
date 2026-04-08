from collections import deque
from aura import config
import time


class WorkingMemory:
    def __init__(self):
        self.items = deque(maxlen=config.WORKING_MEMORY_MAX_ITEMS)
        self.current_task = None
        self.current_context = {}

    def add(self, content: str, item_type: str = "thought"):
        self.items.append(
            {"content": content, "type": item_type, "timestamp": time.time()}
        )

    def get_recent(self, n: int = 10) -> list:
        return list(self.items)[-n:]

    def get_context_string(self) -> str:
        items = self.get_recent(10)
        if not items:
            return "No recent context."
        return "\n".join([f"[{i['type']}]: {i['content']}" for i in items])

    def set_task(self, task: str):
        self.current_task = task
        self.add(f"New task: {task}", "task")

    def clear(self):
        self.items.clear()
        self.current_task = None
