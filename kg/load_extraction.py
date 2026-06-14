"""Load a verified extraction JSON into the graph (the pipeline's load stage).

Run:  python -m kg.load_extraction data/extracted/<file>.json            # DRY RUN
      python -m kg.load_extraction data/extracted/<file>.json --commit   # write

Data-driven: the curated-graph links are NOT hardcoded here. Each extraction's
gold JSON carries a `resolution` block (the human-reviewed propose-don't-merge
result) that this loader reads:

  "resolution": {
    "institutions":  [{"id","name","city"}],               # new :Institution nodes
    "doc_links":     [{"rel","to","confidence?","note?"}],  # (doc)-[rel]->(existing {id})
    "incoming_links":[{"from","from_prop?","rel"}],         # (existing)-[rel]->(doc)  e.g. a citing paper
    "create_nodes":  [{"labels","id","name","props",        # new curated nodes (e.g. a comparator product)
                       "links":[{"rel","dir":"in|out","other"}]}],   # other may be an id or "DOC"
    "author_affiliations": {"<author name>": "<id>", "*": "<default id>"}
  }

Design rules enforced:
  * New extracted facts go into NEW labels keyed by namespaced ids; existing
    curated nodes are only MATCHed and linked, never relabeled.
  * Document is keyed by doi when present, else pmid (handles no-DOI papers).
  * Idempotent (MERGE); DRY RUN by default; existence-checks every MATCH target.
"""

from __future__ import annotations

import json
import sys

from .connection import get_database, get_driver


class Loader:
    def __init__(self, driver, db, commit: bool):
        self.driver = driver
        self.db = db
        self.commit = commit
        self.writes = 0

    def w(self, cypher: str, desc: str, **params):
        if self.commit:
            _, summary, _ = self.driver.execute_query(cypher, database_=self.db, **params)
            c = summary.counters
            self.writes += c.nodes_created + c.relationships_created + c.properties_set
            print(f"  [write] {desc}")
        else:
            print(f"  [dry-run] {desc}")

    def check_exists(self, node_id: str, prop: str = "id") -> bool:
        recs, _, _ = self.driver.execute_query(
            f"MATCH (n {{{prop}: $v}}) RETURN labels(n) AS labels, n.name AS name",
            v=node_id, database_=self.db,
        )
        if recs:
            labels = "".join(f":{l}" for l in recs[0]["labels"])
            print(f"  [match-ok] {prop}={node_id} {labels} ({recs[0]['name']})")
            return True
        print(f"  [MISSING]  {prop}={node_id} -- link will be skipped!")
        return False


def _ns(doc_key: str, local: str) -> str:
    return f"{doc_key}_{local}"


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python -m kg.load_extraction <extraction.json> [--commit]")
        raise SystemExit(2)
    commit = "--commit" in sys.argv
    with open(sys.argv[1], encoding="utf-8") as fh:
        ex = json.load(fh)

    doc = ex["document"]
    res = ex.get("resolution", {})
    key = doc.get("pmc") or doc["pmid"]                  # namespace prefix
    # Document business key: doi when present, else pmid (no-DOI papers).
    dprop, dval = ("doi", doc["doi"]) if doc.get("doi") else ("pmid", doc["pmid"])
    print(f"{'COMMIT' if commit else 'DRY RUN'} load of {doc['title'][:55]}...")
    print(f"namespace={key}  document-key {dprop}={dval}\n")

    # Collect ids we will CREATE (so we don't existence-check our own new nodes).
    created_ids = {i["id"] for i in res.get("institutions", [])}
    created_ids |= {n["id"] for n in res.get("create_nodes", [])}

    with get_driver() as driver:
        db = get_database()
        L = Loader(driver, db, commit)

        # 0. Existence-check every curated node we will MATCH.
        print("# Existence check (curated nodes to link)")
        for dl in res.get("doc_links", []):
            L.check_exists(dl["to"])
        for il in res.get("incoming_links", []):
            L.check_exists(il["from"], il.get("from_prop", "id"))
        for aff in set(res.get("author_affiliations", {}).values()):
            if aff not in created_ids:
                L.check_exists(aff)
        for n in res.get("create_nodes", []):
            for lk in n.get("links", []):
                if lk["other"] != "DOC" and lk["other"] not in created_ids:
                    L.check_exists(lk["other"])

        # 1. Provenance + Document.
        print("\n# Document + provenance")
        L.w("""MERGE (a:ExtractionActivity {id:$id})
               SET a.model=$model, a.status='[VERIFY]'""",
            "ExtractionActivity", id=_ns(key, "EXTRACT"),
            model="extract-article + verify")
        L.w(f"""MERGE (d:Document {{{dprop}:$dval}})
                SET d:Article, d.pmid=$pmid, d.pmc=$pmc, d.doi=$doi, d.title=$title,
                    d.venue=$venue, d.year=$year, d.status='[VERIFY]'""",
            "Document (:Document:Article)", dval=dval, pmid=doc.get("pmid"),
            pmc=doc.get("pmc"), doi=doc.get("doi"), title=doc["title"],
            venue=doc["venue"], year=doc["year"])
        L.w(f"""MATCH (d:Document {{{dprop}:$dval}}), (a:ExtractionActivity {{id:$aid}})
                MERGE (d)-[:WAS_GENERATED_BY]->(a)""",
            "Document -[:WAS_GENERATED_BY]-> ExtractionActivity",
            dval=dval, aid=_ns(key, "EXTRACT"))

        # 2. Outgoing links into the curated graph (ABOUT / DESCRIBES / ...).
        print("\n# Links into the curated graph")
        for dl in res.get("doc_links", []):
            L.w(f"""MATCH (d:Document {{{dprop}:$dval}}), (t {{id:$to}})
                    MERGE (d)-[r:{dl['rel']}]->(t)
                    SET r.confidence=$conf, r.note=$note""",
                f"Document -[:{dl['rel']}]-> {dl['to']}"
                + (f" (conf {dl['confidence']})" if 'confidence' in dl else ""),
                dval=dval, to=dl["to"], conf=dl.get("confidence"), note=dl.get("note", ""))

        # 3. Incoming links (e.g. an already-loaded paper that CITES this one).
        for il in res.get("incoming_links", []):
            fp = il.get("from_prop", "id")
            L.w(f"""MATCH (s {{{fp}:$src}}), (d:Document {{{dprop}:$dval}})
                    MERGE (s)-[:{il['rel']}]->(d)""",
                f"{il['from']} -[:{il['rel']}]-> this Document", src=il["from"], dval=dval)

        # 4. New curated nodes (e.g. a comparator product, organisms).
        for n in res.get("create_nodes", []):
            extra = "".join(f":{l}" for l in n["labels"][1:])
            set_labels = f"x{extra}, " if extra else ""  # avoid invalid "SET x," for single-label nodes
            L.w(f"""MERGE (x:{n['labels'][0]} {{id:$id}}) SET {set_labels}x.name=$name, x += $props""",
                f"create ({':'.join(n['labels'])}) {n['id']}",
                id=n["id"], name=n.get("name", ""), props=n.get("props", {}))
            for lk in n.get("links", []):
                # endpoints: the new node `x`, and `o` (= this Document, or an id node)
                if lk["other"] == "DOC":
                    o_match, o_params = f"(o:Document {{{dprop}:$dval}})", {"dval": dval}
                else:
                    o_match, o_params = "(o {id:$other})", {"other": lk["other"]}
                # dir "in": other -> new ; dir "out": new -> other
                rel = f"(o)-[:{lk['rel']}]->(x)" if lk["dir"] == "in" else f"(x)-[:{lk['rel']}]->(o)"
                L.w(f"MATCH {o_match}, (x {{id:$xid}}) MERGE {rel}",
                    f"  {lk['other']} -[:{lk['rel']}]- {n['id']}",
                    xid=n["id"], **o_params)

        # 5. Institutions + authors (affiliation on the AUTHORED edge).
        print("\n# Authors + institutions")
        for inst in res.get("institutions", []):
            L.w("MERGE (i:Institution {id:$id}) SET i.name=$name, i.city=$city",
                f"Institution {inst['name']}", id=inst["id"], name=inst["name"],
                city=inst.get("city", ""))
        affmap = res.get("author_affiliations", {})
        for au in ex["authors"]:
            target = affmap.get(au["name"], affmap.get("*"))
            L.w(f"""MATCH (d:Document {{{dprop}:$dval}})
                    MERGE (a:Author {{name:$name}})
                    MERGE (a)-[r:AUTHORED]->(d) SET r.affiliation=$aff, r.role=$role""",
                f"Author {au['name']}", dval=dval, name=au["name"],
                aff=au["affiliation"], role=au.get("role", "author"))
            if target:
                L.w("""MATCH (a:Author {name:$name}), (t {id:$tid})
                       MERGE (a)-[:AFFILIATED_WITH]->(t)""",
                    f"  {au['name']} -[:AFFILIATED_WITH]-> {target}",
                    name=au["name"], tid=target)

        # 6. Methods + preparations (the comparison spine).
        print("\n# Methods + preparations")
        for m in ex["methods"]:
            L.w("MERGE (m:Method {id:$id}) SET m.name=$name, m.params=$params",
                f"Method {m['id']} {m['name'][:38]}", id=_ns(key, m["id"]),
                name=m["name"], params=m.get("params", ""))
        for p in ex["preparations"]:
            L.w("MERGE (p:Preparation {id:$id}) SET p.name=$name, p.abbrev=$ab, p.note=$note",
                f"Preparation {p['abbrev']}", id=_ns(key, p["id"]), name=p["name"],
                ab=p.get("abbrev"), note=p.get("note", ""))
            if p.get("produced_by"):
                L.w("""MATCH (p:Preparation {id:$pid}), (m:Method {id:$mid})
                       MERGE (p)-[:PRODUCED_BY]->(m)""",
                    f"  {p['abbrev']} -[:PRODUCED_BY]-> {p['produced_by']}",
                    pid=_ns(key, p["id"]), mid=_ns(key, p["produced_by"]))

        # 7. Claims + reified evidence + conditions.
        print("\n# Claims + evidence + conditions")
        for c in ex["claims"]:
            extra = ":AtomicClaim" if c["tier"] == "atomic" else ":NarrativeClaim"
            L.w(f"""MERGE (c:Claim {{id:$id}})
                    SET c{extra}, c.text=$text, c.tier=$tier, c.basis=$basis,
                        c.stance=$stance, c.confidence=$conf, c.verify=$verify""",
                f"Claim {c['id']} [{c['basis']}/{c['stance']}]", id=_ns(key, c["id"]),
                text=c["text"], tier=c["tier"], basis=c["basis"], stance=c["stance"],
                conf=c["confidence"], verify=c.get("verify", False))
            ev = _ns(key, "EV_" + c["id"])
            L.w(f"""MATCH (d:Document {{{dprop}:$dval}}), (c:Claim {{id:$cid}})
                    MERGE (e:Evidence {{id:$eid}})
                      SET e.quote=$quote, e.figure=$fig, e.confidence=$conf
                    MERGE (d)-[:REPORTS]->(e)
                    MERGE (e)-[:ASSERTS {{stance:$stance}}]->(c)
                    MERGE (e)-[:WAS_DERIVED_FROM]->(d)""",
                f"  Evidence for {c['id']}", dval=dval, cid=_ns(key, c["id"]), eid=ev,
                quote=c.get("quote", ""), fig=c.get("evidence_figure", ""),
                conf=c["confidence"], stance=c["stance"])
            for u in c.get("under", []):
                dim, _, val = u.partition(":")
                if not val:
                    dim, val = "note", u
                L.w("""MATCH (e:Evidence {id:$eid})
                       MERGE (cond:Condition {key:$ckey}) SET cond.dimension=$dim, cond.value=$val
                       MERGE (e)-[:UNDER]->(cond)""",
                    f"    under {dim}:{val[:28]}", eid=ev,
                    ckey=f"{dim.strip()}|{val.strip()}", dim=dim.strip(), val=val.strip())
            for prep_id in c.get("compares", []):
                L.w("""MATCH (c:Claim {id:$cid}), (p:Preparation {id:$pid})
                       MERGE (c)-[:COMPARES]->(p)""",
                    f"    {c['id']} -[:COMPARES]-> {prep_id}",
                    cid=_ns(key, c["id"]), pid=_ns(key, prep_id))
            for ac in c.get("decomposes_to", []):
                L.w("""MATCH (n:Claim {id:$nid}), (a:Claim {id:$aid})
                       MERGE (n)-[:DECOMPOSES_TO]->(a)""",
                    f"    {c['id']} -[:DECOMPOSES_TO]-> {ac}",
                    nid=_ns(key, c["id"]), aid=_ns(key, ac))

        print(f"\nDone. {'Wrote ' + str(L.writes) + ' changes.' if commit else 'DRY RUN - nothing written.'}")


if __name__ == "__main__":
    main()
