"""Dataset lineage manifest: every dataset entering data/ gets registered."""
import json
from datetime import datetime, timezone
from pathlib import Path


def register(manifest_path: Path, name: str, source: str, filters: dict, path: str, rows: int) -> dict:
    if not name or not source:
        raise ValueError("name and source are required")
    entry = {"name": name, "source": source, "filters": filters, "path": path,
             "rows": int(rows), "pulled_at": datetime.now(timezone.utc).isoformat()}
    manifest_path = Path(manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def read_manifest(manifest_path: Path) -> list[dict]:
    p = Path(manifest_path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
