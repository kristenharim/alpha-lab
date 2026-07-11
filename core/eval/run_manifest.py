"""Reproducibility stamp for an experiment run.

Writes ``artifacts/<track>/<variant>_run.json`` next to the scorecard, capturing the
exact params, code version, and time behind a result. Without this, two scorecards
can't be compared later and "why this parameter?" has no answer — the quiet way a
research repo fools itself.

Pairs with ``core/eval/scorecard.py`` (the result) as the *inputs* record.
"""
from __future__ import annotations

import datetime
import json
import subprocess
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
ARTIFACTS = _REPO / "artifacts"


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=_REPO, text=True
        ).strip()
    except Exception:
        return "unknown"


def stamp_run(track: str, variant: str, params: dict, n_trials: int, artifacts_dir=ARTIFACTS) -> Path:
    """Write ``<track>/<variant>_run.json`` and return its path.

    ``n_trials`` must be the HONEST count of variants tried (for deflated Sharpe),
    never 1-by-default. Passing < 1 is a bug, not a shortcut.
    """
    if n_trials < 1:
        raise ValueError("n_trials must be >= 1 (count every variant you tried, not 1)")
    out_dir = Path(artifacts_dir) / track
    out_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "track": track,
        "variant": variant,
        "params": params,
        "n_trials": n_trials,
        "git_sha": _git_sha(),
        "stamped_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    path = out_dir / f"{variant}_run.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True))
    return path


if __name__ == "__main__":
    # self-check: a stamp is complete and reloadable, and n_trials is guarded
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        p = stamp_run("demo", "floor2.0", {"floor": 2.0, "universe": "wide"}, n_trials=7, artifacts_dir=td)
        rec = json.loads(p.read_text())
        assert rec["params"]["floor"] == 2.0 and rec["n_trials"] == 7
        assert rec["git_sha"] and rec["stamped_at"]
        try:
            stamp_run("demo", "bad", {}, 0, artifacts_dir=td)
            raise AssertionError("n_trials=0 must raise")
        except ValueError:
            pass
    print("run_manifest self-check ok")
