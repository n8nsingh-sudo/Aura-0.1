import time
import json
from aura.core.model_router import ModelRouter
from aura.memory.fabric import MemoryFabric


class Goal:
    def __init__(self, description: str, priority: int = 5):
        self.description = description
        self.priority = priority
        self.created_at = time.time()
        self.status = "pending"
        self.subtasks = []


class GoalEngine:
    def __init__(self, router: ModelRouter, memory: MemoryFabric):
        self.router = router
        self.memory = memory
        self.goals = []

    def add_goal(self, description: str, priority: int = 5):
        goal = Goal(description, priority)
        self.goals.append(goal)
        self.goals.sort(key=lambda g: g.priority)
        print(f"Goal added (priority {priority}): {description}")
        return goal

    def generate_subtasks(self, goal: Goal) -> list:
        prompt = f"""You are AURA, an autonomous AI agent.

Goal: {goal.description}

Break this goal into 3-5 specific, actionable subtasks.
Each subtask should be completable in one step.
Return as JSON array of strings.
Example: ["subtask 1", "subtask 2", "subtask 3"]

Return ONLY the JSON array:"""

        response = self.router.think(prompt)

        try:
            response = response.strip()
            if response.startswith("```"):
                response = response.split("\n", 1)[1].rsplit("```", 1)[0]
            subtasks = json.loads(response)
            goal.subtasks = subtasks
            return subtasks
        except Exception as e:
            print(f"Failed to parse subtasks: {e}")
            return [goal.description]

    def get_next_goal(self) -> Goal | None:
        pending = [g for g in self.goals if g.status == "pending"]
        return pending[0] if pending else None

    def generate_autonomous_goals(self) -> list:
        stats = self.memory.get_stats()

        prompt = f"""You are AURA, an autonomous AI agent.

Your current state:
- Total knowledge items: {stats.get("total_knowledge", 0)}
- Working memory items: {stats.get("working_memory_items", 0)}

Generate 3 new goals that would make you more capable and knowledgeable.
Focus on: learning new topics, improving code skills, exploring new domains.

Return as JSON array:
["goal 1", "goal 2", "goal 3"]

Return ONLY the JSON array:"""

        response = self.router.think(prompt)

        try:
            response = response.strip()
            if response.startswith("```"):
                response = response.split("\n", 1)[1].rsplit("```", 1)[0]
            new_goals = json.loads(response)
            for goal_text in new_goals:
                self.add_goal(goal_text, priority=7)
            return new_goals
        except Exception:
            return []
