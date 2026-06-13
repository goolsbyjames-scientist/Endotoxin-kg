"""Introspect an unfamiliar Neo4j graph: labels, relationships, schema, samples.

Run:  python -m kg.explore            (full report, incl. sample nodes)
      python -m kg.explore --schema   (shape only: labels + relationships)

When you're handed a knowledge graph you didn't build, the first job is to learn
its *shape*: what kinds of things (node labels) exist, how they connect
(relationship types), and what properties they carry. Neo4j can report all of
this about the live data — that's what this module does.

This is reusable on ANY Neo4j database, not just ours.
"""

from __future__ import annotations

import sys

from neo4j import Driver

from .connection import get_database, get_driver


def labels(driver: Driver) -> None:
    """Node counts grouped by label (a node may have more than one label)."""
    records, _, _ = driver.execute_query(
        """
        MATCH (n)
        UNWIND labels(n) AS label
        RETURN label, count(*) AS count
        ORDER BY count DESC
        """,
        database_=get_database(),
    )
    print("\n# Node labels")
    for r in records:
        print(f"  {r['count']:>5}  :{r['label']}")


def label_combinations(driver: Driver) -> None:
    """Distinct *sets* of labels nodes carry (nodes can have several labels).

    Many real graphs use a general label (:Product) plus a specific one
    (:LAL / :rFC / :rCR) on the same node. This reveals that layering.
    """
    records, _, _ = driver.execute_query(
        """
        MATCH (n)
        RETURN labels(n) AS combo, count(*) AS count
        ORDER BY count DESC
        """,
        database_=get_database(),
    )
    print("\n# Label combinations (sets of labels per node)")
    for r in records:
        combo = ":" + ":".join(r["combo"]) if r["combo"] else "(no labels)"
        print(f"  {r['count']:>5}  {combo}")


def relationships(driver: Driver) -> None:
    """Relationship counts grouped by type."""
    records, _, _ = driver.execute_query(
        """
        MATCH ()-[r]->()
        RETURN type(r) AS type, count(*) AS count
        ORDER BY count DESC
        """,
        database_=get_database(),
    )
    print("\n# Relationship types")
    for r in records:
        print(f"  {r['count']:>5}  -[:{r['type']}]->")


def schema(driver: Driver) -> None:
    """The connection patterns: (SourceLabel)-[:REL]->(TargetLabel) with counts.

    This is the real 'shape' of the graph — read each row as a sentence.
    """
    records, _, _ = driver.execute_query(
        """
        MATCH (a)-[r]->(b)
        RETURN labels(a)[0] AS src, type(r) AS rel, labels(b)[0] AS dst,
               count(*) AS count
        ORDER BY count DESC
        """,
        database_=get_database(),
    )
    print("\n# Schema (how labels connect)")
    for r in records:
        print(f"  {r['count']:>4}  (:{r['src']})-[:{r['rel']}]->(:{r['dst']})")


def samples(driver: Driver, per_label: int = 2) -> None:
    """A couple of example nodes per label, with all their properties."""
    label_rows, _, _ = driver.execute_query(
        "MATCH (n) UNWIND labels(n) AS l RETURN DISTINCT l AS label ORDER BY label",
        database_=get_database(),
    )
    print(f"\n# Sample nodes ({per_label} per label)")
    for row in label_rows:
        label = row["label"]
        # Label can't be parameterized in Cypher, so we interpolate a known-safe
        # value that came from the DB itself (not user input).
        recs, _, _ = driver.execute_query(
            f"MATCH (n:`{label}`) RETURN properties(n) AS props LIMIT $n",
            n=per_label,
            database_=get_database(),
        )
        print(f"\n  :{label}")
        for rec in recs:
            props = rec["props"]
            # Show the most identifying fields first if present.
            print(f"    - {props}")


def main() -> None:
    # `--schema` prints just the shape (no sample nodes) — compact enough to
    # drop into a skill, a doc, or a prompt as live ground-truth.
    schema_only = "--schema" in sys.argv
    with get_driver() as driver:
        driver.verify_connectivity()
        labels(driver)
        label_combinations(driver)
        relationships(driver)
        schema(driver)
        if not schema_only:
            samples(driver)


if __name__ == "__main__":
    main()
