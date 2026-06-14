"""Read-only entity resolution: match an extraction's candidates to live nodes.

Run:  python -m kg.resolve data/extracted/PMC5302069.json

This is the *propose, don't merge* stage of the ingestion pipeline. It NEVER
writes to the graph — it only runs `MATCH ... RETURN` to find existing nodes that
an extracted entity might correspond to, and prints them for a human to confirm.
The actual linking (MATCH existing / MERGE new) happens in a later, separate step
only after these proposals are reviewed.

Why read-only matters: the BET graph is the owner's curated data. Silently
merging "Seikagaku" from a paper into the wrong company node would corrupt it.
So we surface candidates and let a person decide.
"""

from __future__ import annotations

import json
import sys

from .connection import get_database, get_driver


def _search_by_name(driver, db, fragment: str, label: str | None = None):
    """Find nodes whose name (or id) contains `fragment`, case-insensitive.

    `label` is whitelisted into the query (never raw user input) because labels
    can't be passed as Cypher parameters. The *fragment* is a real $parameter.
    """
    label_clause = f":{label}" if label else ""
    records, _, _ = driver.execute_query(
        f"""
        MATCH (n{label_clause})
        WHERE toLower(coalesce(n.name, '')) CONTAINS toLower($frag)
           OR toLower(coalesce(n.id,   '')) CONTAINS toLower($frag)
        RETURN labels(n) AS labels, n.id AS id, n.name AS name
        ORDER BY name
        LIMIT 10
        """,
        frag=fragment,
        database_=db,
    )
    return records


def _list_label(driver, db, label: str):
    """List all nodes carrying a chemistry label (e.g. rCR, LAL)."""
    records, _, _ = driver.execute_query(
        f"""
        MATCH (n:{label})
        RETURN n.id AS id, n.name AS name
        ORDER BY name
        """,
        database_=db,
    )
    return records


def _print(title: str, records):
    print(f"\n# {title}")
    if not records:
        print("  (no match in graph)")
        return
    for r in records:
        labels = "".join(f":{l}" for l in r["labels"]) if "labels" in r.keys() else ""
        name = r.get("name") or "(no name)"
        print(f"  {r['id']:<16} {name}  {labels}")


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python -m kg.resolve <extraction.json>")
        raise SystemExit(2)

    with open(sys.argv[1], encoding="utf-8") as fh:
        extraction = json.load(fh)

    print(f"Resolving candidates from: {sys.argv[1]}")
    print(f"Document: {extraction['document'].get('title', '?')[:70]}...")

    with get_driver() as driver:
        db = get_database()

        # 1. The manufacturer: does a Seikagaku company node already exist?
        _print("Company candidates for 'Seikagaku'",
               _search_by_name(driver, db, "Seikagaku", "Company"))

        # 2. The natural-lysate comparator product 'Endospecy ES-50M'.
        _print("Product candidates for 'Endospecy'",
               _search_by_name(driver, db, "Endospecy"))
        _print("Product candidates for 'ES-50'",
               _search_by_name(driver, db, "ES-50"))

        # 3. The rCR product family the paper's RCR should map onto.
        _print("All :rCR products in graph", _list_label(driver, db, "rCR"))

        # 4. Where would a natural lysate sit? Show the LAL products.
        _print("All :LAL products in graph", _list_label(driver, db, "LAL"))

        # 5. New institution: Kyushu University (expected: not present).
        _print("Any node matching 'Kyushu'",
               _search_by_name(driver, db, "Kyushu"))

        # 6. What is Seikagaku connected to? The paper's "RCR" name-matches no
        #    product, but Seikagaku's rCR tech is sold under partner brands. See
        #    whether the graph already links them (manufactures / owns / acquired).
        neigh, _, _ = driver.execute_query(
            """
            MATCH (c:Company {id: 'COMP_SEIKAGAKU'})-[rel]-(m)
            RETURN type(rel) AS rel, labels(m) AS labels, m.id AS id, m.name AS name
            ORDER BY rel, name
            """,
            database_=db,
        )
        print("\n# Seikagaku's neighbourhood in the graph")
        if not neigh:
            print("  (Seikagaku has NO relationships — isolated node)")
        for r in neigh:
            labels = "".join(f":{l}" for l in r["labels"])
            print(f"  -[{r['rel']}]- {r['id']:<22} {r['name']}  {labels}")


if __name__ == "__main__":
    main()
