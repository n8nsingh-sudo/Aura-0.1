import time
from collections import defaultdict
from aura import config


class Governor:
    def __init__(self):
        self.request_times = []
        self.daily_cost = 0.0
        self.is_paused = False
        self.total_requests = 0

    def can_make_request(self) -> tuple[bool, str]:
        if self.is_paused:
            return False, "AURA is paused by user"

        if self.daily_cost >= config.MAX_COST_PER_DAY_USD:
            return False, f"Daily cost limit reached: ${self.daily_cost:.2f}"

        now = time.time()
        self.request_times = [t for t in self.request_times if now - t < 60]

        if len(self.request_times) >= config.MAX_REQUESTS_PER_MINUTE:
            return False, f"Rate limit: {config.MAX_REQUESTS_PER_MINUTE} requests/min"

        return True, "OK"

    def record_request(self, tokens_used: int = 0, cost: float = 0.0):
        self.request_times.append(time.time())
        self.daily_cost += cost
        self.total_requests += 1

    def pause(self):
        self.is_paused = True
        print("AURA PAUSED")

    def resume(self):
        self.is_paused = False
        print("AURA RESUMED")

    def reset_daily_cost(self):
        self.daily_cost = 0.0

    def get_status(self) -> dict:
        return {
            "paused": self.is_paused,
            "daily_cost": self.daily_cost,
            "requests_today": self.total_requests,
            "cost_limit": config.MAX_COST_PER_DAY_USD,
        }
