import time
from collections import defaultdict

class FixedWindowLimiter:
    """Fixed window rate limiter"""

    def __init__(self, requests: int, window_seconds: int):
        self.requests = requests
        self.window = window_seconds
        self.counters: dict = defaultdict(lambda: {"count": 0, "window_start": 0})

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        window_start = int(now / self.window) * self.window

        counter = self.counters[key]

        if counter["window_start"] != window_start:
            counter["count"] = 0
            counter["window_start"] = window_start

        if counter["count"] >= self.requests:
            return False

        counter["count"] += 1
        return True

    def get_remaining(self, key: str) -> int:
        """Get remaining requests in current window"""
        now = time.time()
        window_start = int(now / self.window) * self.window

        counter = self.counters[key]

        if counter["window_start"] != window_start:
            return self.requests

        return max(0, self.requests - counter["count"])
