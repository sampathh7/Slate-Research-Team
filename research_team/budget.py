import time
from dataclasses import dataclass, field


class BudgetExceeded(Exception):
    """Raised when a hard limit is hit; the pipeline stops and returns a partial report."""


@dataclass
class Budget:
    max_searches: int = 20
    max_tokens: int = 20_000
    max_seconds: float = 60.0
    searches: int = 0
    tokens: int = 0
    clock: object = time.monotonic
    started: float = field(init=False)

    def __post_init__(self):
        self.started = self.clock()

    def elapsed(self):
        return self.clock() - self.started

    def check_time(self):
        if self.elapsed() > self.max_seconds:
            raise BudgetExceeded("time")

    def charge_search(self, n=1):
        self.check_time()
        if self.searches + n > self.max_searches:
            raise BudgetExceeded("searches")
        self.searches += n

    def charge_tokens(self, n):
        self.check_time()
        if self.tokens + n > self.max_tokens:
            raise BudgetExceeded("tokens")
        self.tokens += n

    def snapshot(self):
        return {"searches": f"{self.searches}/{self.max_searches}",
                "tokens": f"{self.tokens}/{self.max_tokens}",
                "seconds": round(self.elapsed(), 2)}
