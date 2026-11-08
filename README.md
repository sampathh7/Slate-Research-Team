# Slate Research Team

A small multi-agent research pipeline (Planner -> Researcher -> Verifier -> Writer) built to be
testable offline. No API keys needed.

## Run
    python -m research_team "How does an eight-cavity magnetron operate and when was it developed?" --trace trace.jsonl
    python -m unittest discover -s tests
    python evals/run_evals.py

## Design
| Piece | File | What it guarantees |
|---|---|---|
| Budget | budget.py | hard caps on searches, tokens, seconds; overrun returns a *partial* report |
| Trace | trace.py | every plan, search, rejection, claim and verdict logged (JSONL) |
| Search tools | tools.py | cache (hits are free), retries with backoff, failures never cached |
| Source checks | sources.py | blocked domains, too-short, stale, duplicate/mirror pages |
| Claim validation | claims.py | a claim is "supported" only if >=2 independent domains back it; conflicting numbers never count |
| Agents | agents.py | Planner (pronoun-aware, LLM-swappable), Researcher, Verifier, Writer |
| Pipeline | pipeline.py | per-sub-question failure isolation; unsupported claims are never stated as fact |

## Plugging in a real search or LLM
- Search: any object with `.search(query) -> list[Doc]` replaces `CorpusSearch`.
- Planner: `Planner(llm=fn)` where `fn(question) -> str` returns one sub-question per line.

## Known limits
Claim matching is lexical overlap, not semantic entailment; swap `best_support` for an
LLM/NLI judge for production use.

## Live demo
    pip install -r requirements.txt
    streamlit run app.py
Deploy free on Streamlit Community Cloud (main file: `app.py`).
