import threading
import time
from collections import deque


class LoginRateLimiter:
    """Simple in-memory rate limiter for login attempts."""

    def __init__(self, max_attempts: int, window_seconds: int, block_seconds: int):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.block_seconds = block_seconds
        self._lock = threading.Lock()
        self._state = {}

    def _prune_attempts(self, attempts: deque, now: float) -> None:
        cutoff = now - self.window_seconds
        while attempts and attempts[0] < cutoff:
            attempts.popleft()

    def is_blocked(self, key: str) -> tuple[bool, int]:
        now = time.time()
        with self._lock:
            entry = self._state.get(key)
            if not entry:
                return False, 0

            blocked_until = entry.get("blocked_until", 0)
            if blocked_until > now:
                return True, int(blocked_until - now)

            # Unblock expired entries
            attempts = entry.get("attempts", deque())
            self._prune_attempts(attempts, now)
            entry["blocked_until"] = 0
            if not attempts:
                self._state.pop(key, None)
            return False, 0

    def register_failure(self, key: str) -> None:
        now = time.time()
        with self._lock:
            entry = self._state.setdefault(key, {"attempts": deque(), "blocked_until": 0})
            attempts = entry["attempts"]
            self._prune_attempts(attempts, now)
            attempts.append(now)

            if len(attempts) >= self.max_attempts:
                entry["blocked_until"] = now + self.block_seconds
                attempts.clear()

    def register_success(self, key: str) -> None:
        with self._lock:
            self._state.pop(key, None)
