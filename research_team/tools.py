import json
import time
from dataclasses import dataclass
from typing import Optional

from .text import tokens, overlap


class SearchError(Exception):
    pass


@dataclass(frozen=True)
class Doc:
    url: str
    title: str
    text: str
    published: Optional[str] = None


class CorpusSearch:
    """Offline search backend over a JSON corpus. Any object with
    .search(query) -> list[Doc] can replace it (e.g. a real web search)."""

    def __init__(self, docs, fail_on=(), k=5):
        self.docs = list(docs)
        self.fail_on = set(tokens(" ".join(fail_on)))
        self.k = k

    @classmethod
    def from_file(cls, path, **kw):
        with open(path) as f:
            return cls([Doc(**d) for d in json.load(f)], **kw)

    def search(self, query):
        qt = set(tokens(query))
        if self.fail_on & qt:
            raise SearchError(f"backend failure for {query!r}")
        scored = [(overlap(qt, set(tokens(d.title + " " + d.text))), d) for d in self.docs]
        scored = [s for s in scored if s[0] > 0]
        scored.sort(key=lambda s: -s[0])
        return [d for _, d in scored[: self.k]]


class CachedSearch:
    """Wraps a backend with a cache, retries with backoff, and budget accounting.
    Cache hits are free; failures are never cached."""

    def __init__(self, backend, budget, trace, retries=2, backoff=0.1, sleep=time.sleep):
        self.backend, self.budget, self.trace = backend, budget, trace
        self.retries, self.backoff, self.sleep = retries, backoff, sleep
        self.cache = {}

    def search(self, query):
        key = " ".join(sorted(set(tokens(query))))
        if key in self.cache:
            self.trace.log("search", query=query, cached=True, n=len(self.cache[key]))
            return self.cache[key]
        self.budget.charge_search()
        last = None
        for attempt in range(self.retries + 1):
            try:
                docs = self.backend.search(query)
                self.cache[key] = docs
                self.trace.log("search", query=query, cached=False, attempt=attempt, n=len(docs))
                return docs
            except SearchError as e:
                last = e
                self.trace.log("search_error", query=query, attempt=attempt, error=str(e))
                if attempt < self.retries:
                    self.sleep(self.backoff * (2 ** attempt))
        raise SearchError(f"gave up after {self.retries + 1} attempts: {last}")
