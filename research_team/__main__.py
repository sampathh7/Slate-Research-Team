import argparse
from pathlib import Path

from . import Budget, Trace, CorpusSearch, Config, run

p = argparse.ArgumentParser(prog="research_team")
p.add_argument("question")
p.add_argument("--corpus", default=str(Path(__file__).parent.parent / "data" / "corpus.json"))
p.add_argument("--max-searches", type=int, default=20)
p.add_argument("--trace", default=None, help="write JSONL trace to this path")
a = p.parse_args()
rep = run(a.question, CorpusSearch.from_file(a.corpus), Budget(max_searches=a.max_searches),
          Trace(a.trace), Config(blocked=("forum.spam.example",)))
print(rep.markdown)
print("\nbudget:", rep.budget)
