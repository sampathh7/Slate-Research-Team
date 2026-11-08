import json
import time


class Trace:
    """Append-only event log; optionally mirrored to a JSONL file."""

    def __init__(self, path=None):
        self.events = []
        self.path = path
        if path:
            open(path, "w").close()

    def log(self, kind, **data):
        ev = {"seq": len(self.events), "t": round(time.time(), 3), "kind": kind, **data}
        self.events.append(ev)
        if self.path:
            with open(self.path, "a") as f:
                f.write(json.dumps(ev) + "\n")
        return ev

    def of(self, kind):
        return [e for e in self.events if e["kind"] == kind]
