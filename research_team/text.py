import re
from urllib.parse import urlparse

STOP = set("""a an the is are was were be been of in on at to for by with and or it its this
that how what when why which does do did can from as into than then""".split())


def stem(w):
    return w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w


def tokens(text):
    return [stem(w) for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def overlap(a, b):
    """Fraction of set a covered by set b."""
    return len(a & b) / len(a) if a else 0.0


def domain(url):
    d = urlparse(url).netloc.lower()
    return d[4:] if d.startswith("www.") else d
