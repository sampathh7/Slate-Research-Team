import unittest
from datetime import date
from research_team import Budget, BudgetExceeded, Trace, CachedSearch, SearchError, Doc
from research_team.sources import check_source, filter_sources
from research_team.claims import Claim, validate, best_support
from research_team.agents import Planner


class Flaky:
    def __init__(self, fails): self.fails, self.calls = fails, 0
    def search(self, q):
        self.calls += 1
        if self.calls <= self.fails: raise SearchError("boom")
        return [Doc("https://a.example/x", "t", "some long enough text about magnetron things here")]


class Units(unittest.TestCase):
    def test_budget_search_limit(self):
        b = Budget(max_searches=1); b.charge_search()
        with self.assertRaises(BudgetExceeded): b.charge_search()

    def test_budget_time(self):
        t = [0.0]; b = Budget(max_seconds=5, clock=lambda: t[0]); t[0] = 6
        with self.assertRaises(BudgetExceeded): b.charge_tokens(1)

    def test_cache_is_free(self):
        b, f = Budget(), Flaky(0); s = CachedSearch(f, b, Trace(), sleep=lambda x: None)
        s.search("magnetron things"); s.search("things magnetron")
        self.assertEqual((b.searches, f.calls), (1, 1))

    def test_retry_then_success(self):
        s = CachedSearch(Flaky(2), Budget(), Trace(), sleep=lambda x: None)
        self.assertEqual(len(s.search("magnetron")), 1)

    def test_retry_exhausted(self):
        s = CachedSearch(Flaky(9), Budget(), Trace(), retries=1, sleep=lambda x: None)
        with self.assertRaises(SearchError): s.search("magnetron")

    def test_source_checks(self):
        d = lambda u, t, p=None: Doc(u, "t", t, p)
        self.assertFalse(check_source(d("https://bad.example/a", "x" * 50), blocked=("bad.example",))[0])
        self.assertFalse(check_source(d("https://a.example", "short"))[0])
        self.assertFalse(check_source(d("https://a.example", "x" * 50, "2010-01-01"),
                                      max_age_days=365, today=date(2026, 1, 1))[0])
        seen = set(); txt = "a reasonably long sentence about klystrons and cavities."
        kept, rej = filter_sources([d("https://a.example", txt), d("https://b.example", txt)], seen)
        self.assertEqual((len(kept), rej[0][1]), (1, "duplicate"))

    def test_number_conflict_not_support(self):
        doc = Doc("https://a.example", "t", "The magnetron was developed in 1985 for radar use.")
        self.assertEqual(best_support("The magnetron was developed in 1940 for radar use.", doc)[0], 0.0)

    def test_independent_domains_required(self):
        c = Claim("The reflex klystron uses a repeller electrode.", "https://a.example/1", "q", 1)
        same = [Doc("https://a.example/1", "t", c.text), Doc("https://a.example/2", "t", c.text)]
        self.assertEqual(validate(c, same).status, "weak")
        other = same + [Doc("https://b.example/1", "t", c.text)]
        self.assertEqual(validate(c, other).status, "supported")

    def test_planner_pronoun(self):
        subs = Planner().plan("How does an eight-cavity magnetron operate and when was it developed?")
        self.assertEqual(len(subs), 2); self.assertIn("magnetron", subs[1])


if __name__ == "__main__":
    unittest.main()
