"""End-to-end evals on the offline corpus. Run: python evals/run_evals.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from research_team import Budget, Trace, CorpusSearch, Config, run

CORPUS = str(Path(__file__).parent.parent / "data" / "corpus.json")
CFG = Config(blocked=("forum.spam.example",))


def go(q, fail_on=(), **bkw):
    rep = run(q, CorpusSearch.from_file(CORPUS, fail_on=fail_on), Budget(**bkw), Trace(), CFG,
              sleep=lambda x: None)
    return rep


def supported(rep): return " ".join(r.claim.text for r in rep.results if r.status == "supported")


def e_grounded():
    r = go("How does an eight-cavity magnetron operate and when was it developed?")
    return "pi mode" in supported(r) and "1940" in supported(r)

def e_rejects_spam():
    r = go("How does an eight-cavity magnetron operate and when was it developed?")
    return "1985" not in r.markdown and "spam" not in r.markdown

def e_tuning():
    return "repeller voltage" in supported(go("How is a reflex klystron tuned electronically?"))

def e_abstains():
    r = go("What is the price of a magnetron in rupees?")
    return not supported(r) and "Insufficient evidence" in r.markdown

def e_failure_isolation():
    r = go("What is a reflex klystron and when was the magnetron developed?", fail_on=("magnetron",))
    return len(r.failures) == 1 and "single-cavity" in supported(r) and "Gaps" in r.markdown

def e_budget_partial():
    r = go("What is a reflex klystron and when was the magnetron developed?", max_searches=1)
    return r.partial == "searches" and "Partial result" in r.markdown and "single-cavity" in supported(r)

def e_trace_complete():
    r = go("How is a reflex klystron tuned electronically?")
    cands = {e["text"] for e in r.trace.of("claim_candidate")}
    verdicts = {e["text"] for e in r.trace.of("claim_verdict")}
    return cands == verdicts and len(r.trace.of("report")) == 1

def e_every_finding_cited():
    r = go("How does an eight-cavity magnetron operate and when was it developed?")
    finds = r.markdown.split("## Verified findings")[1].split("##")[0].strip().splitlines()
    return all(l.rstrip().endswith("]") for l in finds)

EVALS = [e_grounded, e_rejects_spam, e_tuning, e_abstains, e_failure_isolation,
         e_budget_partial, e_trace_complete, e_every_finding_cited]

if __name__ == "__main__":
    fails = 0
    for e in EVALS:
        ok = e(); fails += not ok
        print(("PASS" if ok else "FAIL"), e.__name__)
    print(f"\n{len(EVALS) - fails}/{len(EVALS)} passed")
    sys.exit(1 if fails else 0)
