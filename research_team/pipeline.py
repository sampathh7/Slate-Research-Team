from dataclasses import dataclass, field

from .agents import Planner, Researcher, Verifier, Writer
from .budget import Budget, BudgetExceeded
from .tools import CachedSearch, SearchError
from .trace import Trace


@dataclass
class Config:
    min_sources: int = 2
    threshold: float = 0.5
    blocked: tuple = ()
    max_age_days: int = None
    per_subq: int = 4


@dataclass
class Report:
    question: str
    markdown: str
    results: list
    failures: list
    partial: str
    budget: dict
    trace: Trace = field(repr=False, default=None)


def run(question, backend, budget=None, trace=None, config=None, planner=None, sleep=None):
    budget, trace, cfg = budget or Budget(), trace or Trace(), config or Config()
    kw = {"sleep": sleep} if sleep else {}
    search = CachedSearch(backend, budget, trace, **kw)
    researcher = Researcher(search, budget, trace,
                            {"blocked": cfg.blocked, "max_age_days": cfg.max_age_days},
                            cfg.threshold, cfg.per_subq)
    subqs = (planner or Planner()).plan(question)
    trace.log("plan", subqs=subqs)

    docs, claims, failures, partial = {}, [], [], ""
    for sq in subqs:
        try:
            kept, found = researcher.research(sq)   # failures are isolated per sub-question
            docs.update({d.url: d for d in kept})
            claims += found
        except BudgetExceeded as e:
            partial = str(e)
            trace.log("budget_exceeded", limit=partial, at=sq)
            break
        except Exception as e:
            failures.append({"subq": sq, "error": str(e)})
            trace.log("failure", subq=sq, error=str(e))

    results = Verifier(trace, cfg.min_sources, cfg.threshold).verify(claims, list(docs.values()))
    md = Writer().write(question, results, failures, partial, docs)
    trace.log("report", supported=sum(r.status == "supported" for r in results),
              weak=sum(r.status == "weak" for r in results), failures=len(failures))
    return Report(question, md, results, failures, partial, budget.snapshot(), trace)
