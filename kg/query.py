"""Query the Bacterial Endotoxins Testing graph from Python and print results.

Run:  python -m kg.query

This is the *programmatic* counterpart to cypher/examples.cypher: instead of a
drawing in Neo4j Browser, you get plain Python data you could feed into an app,
a notebook, or an LLM prompt.

KEY DRIVER CONCEPTS shown here:
  - driver.execute_query(...) runs one query in its own transaction and returns
    (records, summary, keys). Each record acts like a dict keyed by the RETURN
    names.
  - Pass values as $parameters (kept separate from the query text) rather than
    formatting them into the string — safer, and lets Neo4j cache the plan.
"""

from __future__ import annotations

from neo4j import Driver

from .connection import get_database, get_driver


def products_by_chemistry(driver: Driver) -> None:
    """Aggregate products by reagent chemistry — the LAL vs recombinant split."""
    records, _, _ = driver.execute_query(
        """
        MATCH (c:Company)-[:MANUFACTURES]->(p:Product)
        RETURN p.chemistry AS chemistry,
               count(*) AS products,
               collect(DISTINCT c.name)[..4] AS some_makers
        ORDER BY products DESC
        """,
        database_=get_database(),
    )
    print("\n# Products by chemistry (LAL = animal-derived, rFC/rCR = recombinant)")
    for r in records:
        makers = ", ".join(r["some_makers"])
        print(f"  {r['products']:>2}  {r['chemistry']:<13} e.g. {makers}")


def recombinant_makers(driver: Driver) -> None:
    """Two labels at once: companies making any rFC OR rCR product.

    `p:rFC OR p:rCR` tests for chemistry labels on the product node.
    """
    records, _, _ = driver.execute_query(
        """
        MATCH (c:Company)-[:MANUFACTURES]->(p:Product)
        WHERE p:rFC OR p:rCR
        RETURN c.name AS company, collect(p.name) AS products
        ORDER BY company
        """,
        database_=get_database(),
    )
    print("\n# Companies offering recombinant (animal-free) assays")
    for r in records:
        print(f"  {r['company']:<28} {', '.join(r['products'])}")


def methods_recognizing(driver: Driver, chemistry: str = "rFC") -> None:
    """Which compendial methods recognize a given chemistry? Parameterized.

    The property name is built from a *whitelisted* chemistry, never raw input,
    because property keys can't be passed as Cypher parameters.
    """
    prop = {"LAL": "recognizes_LAL", "rFC": "recognizes_rFC", "rCR": "recognizes_rCR"}[
        chemistry
    ]
    records, _, _ = driver.execute_query(
        f"""
        MATCH (m:CompendialMethod)
        WHERE m.{prop} = true
        RETURN m.name AS method, m.title AS title, m.effective_year AS since
        ORDER BY since, method
        """,
        database_=get_database(),
    )
    print(f"\n# Compendial methods that recognize {chemistry}")
    for r in records:
        since = f" (since {r['since']})" if r["since"] else ""
        print(f"  {r['method']:<18} {r['title']}{since}")


def acquisition_chains(driver: Driver) -> None:
    """Variable-length paths: the longest corporate-acquisition lineages.

    [:ACQUIRED*1..6] follows 1–6 ACQUIRED hops. We keep only the longest chain
    ending at each company (no further acquirer above the start).
    """
    records, _, _ = driver.execute_query(
        """
        MATCH path = (top:Company)-[:ACQUIRED*1..6]->(bottom:Company)
        WHERE NOT ()-[:ACQUIRED]->(top)        // start at an ultimate acquirer
          AND NOT (bottom)-[:ACQUIRED]->()      // end at a leaf that bought no one
        RETURN [n IN nodes(path) | n.name] AS chain, length(path) AS hops
        ORDER BY hops DESC, chain
        """,
        database_=get_database(),
    )
    print("\n# Corporate acquisition lineages (longest chains)")
    for r in records:
        print(f"  {r['hops']} hops:  " + "  →  ".join(r["chain"]))


def europe_recombinant_supply(driver: Driver) -> None:
    """A real supply question answered by one graph pattern.

    'Companies HQ'd anywhere within Europe that make a recombinant assay.'
    Joins region hierarchy (PART_OF*) with chemistry labels.
    """
    records, _, _ = driver.execute_query(
        """
        MATCH (c:Company)-[:HEADQUARTERED_IN]->(:Region)-[:PART_OF*0..2]->(:Region {name: 'Europe'})
        MATCH (c)-[:MANUFACTURES]->(p:Product)
        WHERE p:rFC OR p:rCR
        RETURN c.name AS company, collect(DISTINCT p.name) AS products
        ORDER BY company
        """,
        database_=get_database(),
    )
    print("\n# European-HQ'd companies making recombinant assays")
    if not records:
        print("  (none)")
    for r in records:
        print(f"  {r['company']:<24} {', '.join(r['products'])}")


def most_connected(driver: Driver) -> None:
    """Degree centrality across the whole graph: the hub nodes."""
    records, _, _ = driver.execute_query(
        """
        MATCH (n)
        RETURN coalesce(n.name, n.number, n.id) AS name,
               labels(n)[0] AS label,
               count { (n)--() } AS degree
        ORDER BY degree DESC
        LIMIT 8
        """,
        database_=get_database(),
    )
    print("\n# Most connected nodes (degree)")
    for r in records:
        print(f"  {r['degree']:>2}  {r['name']} ({r['label']})")


def main() -> None:
    with get_driver() as driver:
        driver.verify_connectivity()
        products_by_chemistry(driver)
        recombinant_makers(driver)
        methods_recognizing(driver, "rFC")
        acquisition_chains(driver)
        europe_recombinant_supply(driver)
        most_connected(driver)
    print(
        "\nTip: copy any of these queries into Neo4j Browser to SEE the same "
        "relationships drawn as a graph, or edit cypher/examples.cypher to explore further."
    )


if __name__ == "__main__":
    main()
