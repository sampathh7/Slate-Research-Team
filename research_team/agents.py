"""Four small agents. Each is deterministic by default; pass `llm` (a callable
str -> str) to Planner to swap in model-based planning."""
import re

from .budget import BudgetExceeded
from .claims import extract_claims, validate, dedupe
from .sources import filter_sources
from .text import tokens

PRONOUNS = {"it", "its", "they", "their", "this", "these"}


class Planner:
    def __init__(self, llm=None, max_subqs=4):
        self.llm, self.max_subqs = llm, max_subqs

    def plan(self, question):
        if self.llm:
            lines = [l.strip("-• ").strip() for l in self.llm(question).splitlines() if l.strip()]
            return lines[: self.max_subqs] or [question]
        parts = [p.strip(" ?.") for p in re.split(r"\s+and\s+|;", question)]
        parts = [p for p in parts if len(p.split()) >= 3]
        if len(parts) < 2:
            return [question.strip()]
        anchor = " ".join(tokens(parts[0]))
        out = []
        for i, p in enumerate(parts[: self.max_subqs]):
            # resolve pronouns by borrowing the first clause's subject words
            if i and PRONOUNS & set(re.findall(r"[a-z]+", p.lower())):
                p = f"{p} {anchor}"
            out.append(p + "?")
        return out


class Researcher:
    def __init__(self, search, budget, trace, source_kw=None, claim_threshold=0.5, per_subq=4):
        self.search, self.budget, self.trace = search, budget, trace
        self.source_kw = source_kw or {}
        self.claim_threshold, self.per_subq = claim_threshold, per_subq
        self.seen = set()

    def research(self, subq):
        docs = self.search.search(subq)
        kept, rejected = filter_sources(docs, self.seen, **self.source_kw)
        for doc, why in rejected:
            self.trace.log("source_rejected", url=doc.url, reason=why)
        claims = []
        for doc in kept:
            self.budget.charge_tokens(len(doc.text) // 4)
            claims += extract_claims(doc, subq, self.claim_threshold)
        claims = dedupe(sorted(claims, key=lambda c: -c.score))[: self.per_subq]
        for c in claims:
            self.trace.log("claim_candidate", subq=subq, url=c.url, text=c.text)
        return kept, claims


class Verifier:
    def __init__(self, trace, min_sources=2, threshold=0.5):
        self.trace, self.min_sources, self.threshold = trace, min_sources, threshold

    def verify(self, claims, docs):
        results = []
        for c in claims:
            r = validate(c, docs, self.min_sources, self.threshold)
            self.trace.log("claim_verdict", text=c.text, status=r.status,
                           sources=[u for u, _ in r.support.values()])
            results.append(r)
        return results


class Writer:
    def write(self, question, results, failures, partial, docs):
        good = [r for r in results if r.status == "supported"]
        weak = [r for r in results if r.status == "weak"]
        order = []

        def cite(r):
            nums = []
            for url, _ in r.support.values():
                if url not in order:
                    order.append(url)
                nums.append(order.index(url) + 1)
            return "".join(f"[{n}]" for n in sorted(set(nums)))

        out = [f"# Research report", f"**Question:** {question}", ""]
        if partial:
            out += [f"> Partial result: stopped early ({partial}).", ""]
        out.append("## Verified findings")
        out += [f"- {r.claim.text} {cite(r)}" for r in good] or \
               ["- Insufficient evidence: no claim was confirmed by independent sources."]
        if weak:
            out += ["", "## Unverified (single source)"]
            out += [f"- {r.claim.text} {cite(r)}" for r in weak]
        if failures:
            out += ["", "## Gaps"]
            out += [f"- {f['subq']}: {f['error']}" for f in failures]
        out += ["", "## Sources"]
        out += [f"[{i}] {docs[u].title} ({u})" for i, u in enumerate(order, 1)]
        return "\n".join(out)
