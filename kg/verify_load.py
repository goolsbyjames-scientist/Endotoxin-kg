"""Quick read-only sanity check after loading an extraction.

Run:  python -m kg.verify_load

Confirms the PMC5302069 load landed and demonstrates the queries the load makes
possible — especially the patent <-> peer-reviewed-article tie.
"""

from __future__ import annotations

from .connection import get_database, get_driver

DOI = "10.1177/1753425916681074"


def main() -> None:
    with get_driver() as driver:
        db = get_database()

        def q(cypher, **p):
            recs, _, _ = driver.execute_query(cypher, database_=db, **p)
            return recs

        # 1. What did this Document bring into the graph?
        print("# Node counts attached to the Document")
        rows = q(
            """
            MATCH (d:Document {doi:$doi})
            OPTIONAL MATCH (d)<-[:AUTHORED]-(a:Author)
            OPTIONAL MATCH (d)-[:REPORTS]->(e:Evidence)-[:ASSERTS]->(c:Claim)
            RETURN count(DISTINCT a) AS authors,
                   count(DISTINCT e) AS evidence,
                   count(DISTINCT c) AS claims
            """,
            doi=DOI,
        )
        r = rows[0]
        print(f"  authors={r['authors']}  evidence={r['evidence']}  claims={r['claims']}")

        # 2. THE PAYOFF: which patents does this article describe?
        print("\n# Patent <-> article tie: paper -[:DESCRIBES]-> patents")
        for r in q(
            """
            MATCH (d:Document {doi:$doi})-[rel:DESCRIBES]->(p:Patent)
            RETURN p.id AS patent, rel.confidence AS conf, rel.note AS note
            ORDER BY conf DESC
            """,
            doi=DOI,
        ):
            note = f"  <- {r['note']}" if r["note"] else ""
            print(f"  {r['patent']:<22} conf={r['conf']}{note}")

        # 3. Experimental vs theoretical claim split (the basis distinction).
        print("\n# Claim basis split (experimental = demonstrated, theoretical = argued)")
        for r in q(
            """
            MATCH (d:Document {doi:$doi})-[:REPORTS]->(:Evidence)-[:ASSERTS]->(c:Claim)
            RETURN c.basis AS basis, count(*) AS n
            ORDER BY n DESC
            """,
            doi=DOI,
        ):
            print(f"  {r['basis']:<14} {r['n']}")

        # 4. Cross-over: extracted claims now reference curated/new products.
        print("\n# A claim comparing the RCR against the (new) Endospecy product")
        for r in q(
            """
            MATCH (c:Claim)-[:COMPARES]->(p:Preparation)
            WHERE p.abbrev IN ['RCR','ES-50M']
            WITH c, collect(p.abbrev) AS preps
            WHERE 'RCR' IN preps AND 'ES-50M' IN preps
            RETURN c.id AS claim, c.basis AS basis, left(c.text, 80) AS text
            ORDER BY claim
            """
        ):
            print(f"  {r['claim']:<5} [{r['basis']}] {r['text']}...")

        # 5. Cross-paper: the document citation network (the payoff of paper #2).
        print("\n# Document citation network")
        for r in q(
            """
            MATCH (a:Document)-[:CITES]->(b:Document)
            RETURN coalesce(a.pmc, a.pmid) AS citing, a.year AS cy,
                   coalesce(b.pmc, b.pmid) AS cited, b.year AS by,
                   left(b.title, 50) AS title
            """
        ):
            print(f"  {r['citing']} ({r['cy']}) -[:CITES]-> {r['cited']} ({r['by']}) {r['title']}...")

        # 6. Every Document now in the graph, with its claim count + basis mix.
        print("\n# Documents in the graph")
        for r in q(
            """
            MATCH (d:Document)
            OPTIONAL MATCH (d)-[:REPORTS]->(:Evidence)-[:ASSERTS]->(c:Claim)
            RETURN coalesce(d.pmc, d.pmid) AS id, d.year AS year,
                   count(c) AS claims, collect(DISTINCT c.basis) AS bases
            ORDER BY year
            """
        ):
            print(f"  {r['id']:<12} {r['year']}  {r['claims']} claims  bases={r['bases']}")


if __name__ == "__main__":
    main()
