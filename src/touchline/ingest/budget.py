"""A request budget that bounds how much a run is allowed to download.

Downloads are rate- and count-limited so an acquisition run cannot accidentally
hammer a provider or run unbounded. The budget is explicit state so a resumed run
continues from where it stopped rather than starting the count again.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


class BudgetExceeded(RuntimeError):
    """Raised when a request would exceed the configured budget."""


@dataclass
class RequestBudget:
    """Bounds total requests and enforces a minimum spacing between them.

    Parameters
    ----------
    max_requests:
        Hard cap on requests for the whole run.
    min_interval_s:
        Minimum seconds between successive requests (simple politeness throttle).
    """

    max_requests: int
    min_interval_s: float = 0.0
    _used: int = field(default=0, init=False)
    _last_ts: float = field(default=0.0, init=False)

    @property
    def used(self) -> int:
        return self._used

    @property
    def remaining(self) -> int:
        return max(0, self.max_requests - self._used)

    def acquire(self, sleeper=time.sleep, clock=time.monotonic) -> None:
        """Account for one request, blocking for the throttle if needed.

        ``sleeper`` and ``clock`` are injectable so tests can run without real
        waiting.
        """
        if self._used >= self.max_requests:
            raise BudgetExceeded(
                f"request budget of {self.max_requests} exhausted"
            )
        now = clock()
        if self._last_ts and self.min_interval_s > 0:
            wait = self.min_interval_s - (now - self._last_ts)
            if wait > 0:
                sleeper(wait)
                now = clock()
        self._used += 1
        self._last_ts = now

    def snapshot(self) -> dict:
        """Serialisable state for resuming a run."""
        return {"max_requests": self.max_requests, "used": self._used}

    @classmethod
    def restore(cls, state: dict) -> RequestBudget:
        b = cls(max_requests=int(state["max_requests"]))
        b._used = int(state.get("used", 0))
        return b
