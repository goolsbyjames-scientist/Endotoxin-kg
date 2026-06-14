"""Hands-off ingestion pipeline: load a verified extraction, then keep all in sync.

Run:  python -m kg.pipeline data/extracted/PMC5302069.json            # dry-run
      python -m kg.pipeline data/extracted/PMC5302069.json --commit   # do it

Run this AFTER a human has reviewed the extraction (kg.review) and approved it.
From here there is no human judgment left — only logistics:

  1. load     -> MERGE new nodes + MATCH-link to the curated graph
  2. embed    -> embed the new :Claim / :Document nodes for semantic search
  3. snapshot -> regenerate the schema snapshot the endotoxin-graph skill reads

Resolution writes follow the 'auto-write, flag low-confidence' policy implemented
in kg.load_extraction: links are written with a confidence and anything below
threshold carries a [VERIFY] note, so the run is hands-off yet fully auditable.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# The schema snapshot the endotoxin-graph skill reads for orientation.
SNAPSHOT = Path(".claude/skills/endotoxin-graph/schema-snapshot.md")


def _run(args: list[str], desc: str) -> None:
    print(f"\n=== {desc} ===")
    result = subprocess.run([sys.executable, "-m", *args])
    if result.returncode != 0:
        print(f"!! step failed ({desc}); stopping.")
        raise SystemExit(result.returncode)


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python -m kg.pipeline <extraction.json> [--commit]")
        raise SystemExit(2)
    json_path = sys.argv[1]
    commit = "--commit" in sys.argv

    # Keep this orchestrator's own output ASCII: unlike the kg.* modules it does
    # not import connection.py (which forces UTF-8 on stdout), so non-ASCII here
    # would crash on Windows' cp1252 console.
    if not commit:
        print("DRY RUN -- showing the load plan only. Pass --commit to load/embed/snapshot.\n")
        _run(["kg.load_extraction", json_path], "1/3 load (dry-run)")
        print("\n(embed + snapshot steps run only with --commit)")
        return

    _run(["kg.load_extraction", json_path, "--commit"], "1/3 load -> graph")
    _run(["kg.embeddings", "--extraction"], "2/3 embed new :Claim / :Document nodes")
    _run(["kg.explore", "--schema", "--write", str(SNAPSHOT)], "3/3 regenerate schema snapshot")
    print("\n[OK] Pipeline complete -- graph, embeddings, and schema snapshot are in sync.")


if __name__ == "__main__":
    main()
