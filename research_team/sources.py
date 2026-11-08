from datetime import date

from .text import tokens, domain


def check_source(doc, blocked=(), min_chars=40, max_age_days=None, today=None):
    d = domain(doc.url)
    if any(d == b or d.endswith("." + b) for b in blocked):
        return False, "blocked domain"
    if len(doc.text.strip()) < min_chars:
        return False, "too short"
    if max_age_days and doc.published:
        age = ((today or date.today()) - date.fromisoformat(doc.published)).days
        if age > max_age_days:
            return False, f"stale ({age}d)"
    return True, "ok"


def filter_sources(docs, seen, **kw):
    """Split docs into (kept, rejected[(doc, reason)]). `seen` dedupes urls and
    near-identical mirrors across the whole run."""
    kept, rejected = [], []
    for doc in docs:
        ok, why = check_source(doc, **kw)
        key = " ".join(tokens(doc.text))
        if ok and (doc.url in seen or key in seen):
            ok, why = False, "duplicate"
        if ok:
            seen.update([doc.url, key])
            kept.append(doc)
        else:
            rejected.append((doc, why))
    return kept, rejected
