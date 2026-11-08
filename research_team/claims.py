from dataclasses import dataclass, field

from .text import tokens, sentences, overlap, domain


@dataclass
class Claim:
    text: str
    url: str
    subq: str
    score: float


@dataclass
class ClaimResult:
    claim: Claim
    status: str  # supported | weak | unsupported
    support: dict = field(default_factory=dict)  # domain -> (url, evidence sentence)


def extract_claims(doc, query, threshold=0.5, limit=2):
    qt = set(tokens(query))
    found = []
    for s in sentences(doc.text):
        st = set(tokens(s))
        sc = overlap(qt, st)
        if sc >= threshold and len(st) >= 3:
            found.append(Claim(s, doc.url, query, sc))
    found.sort(key=lambda c: -c.score)
    return found[:limit]


def best_support(claim_text, doc):
    """Best-matching sentence in doc. A sentence missing any number in the claim
    scores 0, so conflicting figures never count as agreement."""
    ct = set(tokens(claim_text))
    nums = {t for t in ct if t.isdigit()}
    best = (0.0, "")
    for s in sentences(doc.text):
        st = set(tokens(s))
        if nums and not nums <= st:
            continue
        sc = overlap(ct, st)
        if sc > best[0]:
            best = (sc, s)
    return best


def validate(claim, docs, min_sources=2, threshold=0.5):
    support = {}
    for doc in docs:
        sc, sent = best_support(claim.text, doc)
        d = domain(doc.url)
        if sc >= threshold and d not in support:
            support[d] = (doc.url, sent)
    n = len(support)
    status = "supported" if n >= min_sources else "weak" if n else "unsupported"
    return ClaimResult(claim, status, support)


def dedupe(claims, jaccard=0.7):
    out = []
    for c in claims:
        ct = set(tokens(c.text))
        if not any(len(ct & set(tokens(o.text))) / len(ct | set(tokens(o.text))) >= jaccard for o in out):
            out.append(c)
    return out
