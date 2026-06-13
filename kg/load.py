"""Run a .cypher file against the database, statement by statement.

Usage:
    python -m kg.load                       # list the .cypher files you can run
    python -m kg.load cypher/<file>.cypher  # execute one file

WHY SPLIT STATEMENTS OURSELVES?
The Neo4j driver's `session.run()` executes ONE Cypher statement per call.
A .cypher file can hold several statements separated by ';'. So we read the
file, strip '//' comments, split on ';', and run the pieces in order.

This naive splitter assumes simple, self-contained statements (no ';' inside a
string literal). That holds for the files in `cypher/`. For complex scripts you
would instead use cypher-shell or Neo4j Browser's :source command.

NOTE: the real domain graph in this database was NOT created by this project —
it was already present. So there is no "seed" step here; this module is a
general-purpose runner, handy for one-offs like cypher/remove_toy_seed.cypher.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from neo4j import Driver

from .connection import get_database, get_driver

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CYPHER_DIR = _PROJECT_ROOT / "cypher"


def _split_statements(text: str) -> list[str]:
    """Turn a multi-statement .cypher file into a list of runnable statements.

    1. Drop full-line '//' comments.   2. Split on ';'.   3. Trim + drop empties.
    """
    no_comments = "\n".join(
        line for line in text.splitlines() if not line.strip().startswith("//")
    )
    parts = re.split(r";\s*(?:\n|$)", no_comments)
    return [p.strip() for p in parts if p.strip()]


def run_cypher_file(driver: Driver, path: Path) -> None:
    """Execute every statement in a .cypher file, in order, in one session."""
    statements = _split_statements(path.read_text(encoding="utf-8"))
    db = get_database()
    print(f"\n=== {path.name} ({len(statements)} statement(s)) ===")
    with driver.session(database=db) as session:
        for i, stmt in enumerate(statements, start=1):
            preview = " ".join(stmt.split())[:70]
            print(f"  [{i}/{len(statements)}] {preview}...")
            summary = session.run(stmt).consume()  # forces execution; surfaces errors
            counters = summary.counters
            # Show what changed, so destructive runs are transparent.
            changes = {
                k: v
                for k, v in {
                    "nodes_created": counters.nodes_created,
                    "nodes_deleted": counters.nodes_deleted,
                    "relationships_created": counters.relationships_created,
                    "relationships_deleted": counters.relationships_deleted,
                    "properties_set": counters.properties_set,
                }.items()
                if v
            }
            if changes:
                print(f"        -> {changes}")
    print(f"=== {path.name} done ===")


def _list_cypher_files() -> None:
    print("Available .cypher files (pass one as an argument):\n")
    for f in sorted(_CYPHER_DIR.glob("*.cypher")):
        print(f"  python -m kg.load cypher/{f.name}")
    print("\nNote: cypher/examples.cypher is meant for Neo4j Browser, not this runner.")


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        _list_cypher_files()
        return

    path = Path(args[0])
    if not path.is_absolute():
        path = _PROJECT_ROOT / path
    if not path.exists():
        sys.exit(f"No such file: {path}")

    with get_driver() as driver:
        driver.verify_connectivity()
        run_cypher_file(driver, path)


if __name__ == "__main__":
    main()
