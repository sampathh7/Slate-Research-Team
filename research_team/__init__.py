"""Slate Research Team: a small, testable multi-agent research pipeline."""
from .budget import Budget, BudgetExceeded
from .trace import Trace
from .tools import CorpusSearch, CachedSearch, SearchError, Doc
from .pipeline import run, Config, Report

__all__ = ["Budget", "BudgetExceeded", "Trace", "CorpusSearch", "CachedSearch",
           "SearchError", "Doc", "run", "Config", "Report"]
