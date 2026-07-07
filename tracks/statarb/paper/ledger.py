"""Append-only JSONL ledgers — one immutable row per event, four logs under one dir.

Every number in the resolver reconstructs from these (registry.register ethos: you
never mutate a row, you append the next event). The four logs and their rows are in
the spec's logging table; this module is just the writer/reader, no policy.
"""
import json
from pathlib import Path

LOGS = ("targets", "fills", "positions", "daily_nav")


class Ledger:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def append(self, log: str, row: dict) -> None:
        with open(self.root / f"{log}.jsonl", "a") as f:
            f.write(json.dumps(row, default=str) + "\n")

    def read(self, log: str) -> list[dict]:
        p = self.root / f"{log}.jsonl"
        if not p.exists():
            return []
        return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
