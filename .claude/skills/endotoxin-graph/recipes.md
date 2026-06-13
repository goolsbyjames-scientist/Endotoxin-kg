# BET graph — query recipes

Copy-paste Cypher for common question shapes. All are **read-only**. Paste into
Neo4j Browser to see them drawn, or run from Python via
`driver.execute_query(cypher, **params, database_=get_database())`.

> Filter chemistry with label tests (`p:rFC OR p:rCR`), not properties.

## Recombinant adoption — who has moved past LAL?

```cypher
MATCH (c:Company)-[:MANUFACTURES]->(p:Product)
WHERE p:rFC OR p:rCR
RETURN c.name AS company, collect(p.name) AS recombinant_products
ORDER BY company;
```

## Which compendial methods recognize which products (and chemistries)?

```cypher
MATCH (m:CompendialMethod)-[:RECOGNIZES]->(p:Product)
RETURN m.name AS method, p.chemistry AS chemistry, count(*) AS products
ORDER BY method, chemistry;
```

## Patent expiry — what IP is still blocking, and what it protects?

```cypher
MATCH (c:Company)-[:OWNS_PATENT]->(pat:Patent)-[:PROTECTS]->(prod:Product)
RETURN c.name AS owner, pat.number AS patent, pat.status AS status,
       pat.expiration_year AS expires, collect(DISTINCT prod.name) AS protects
ORDER BY expires;
```

## Regulatory chain — which guidances reference which methods, in which regions?

```cypher
MATCH (rd:RegulatoryDocument)-[:REFERENCES]->(m:CompendialMethod)
OPTIONAL MATCH (rd)-[:IN_FORCE_IN]->(r:Region)
RETURN rd.name AS document, collect(DISTINCT m.name) AS references_methods,
       collect(DISTINCT r.name) AS regions
ORDER BY document;
```

## Segment coverage — which products serve a given market segment?

```cypher
MATCH (p:Product)-[:SERVES_SEGMENT]->(s:Segment {name: $segment})
RETURN s.name AS segment, p.chemistry AS chemistry,
       collect(p.name) AS products
ORDER BY chemistry;
// params: { segment: 'Medical Device Manufacturing' }
```

## Corporate lineage — acquisition chains (variable-length path)

```cypher
MATCH path = (top:Company)-[:ACQUIRED*1..6]->(bottom:Company)
WHERE NOT ()-[:ACQUIRED]->(top) AND NOT (bottom)-[:ACQUIRED]->()
RETURN [n IN nodes(path) | n.name] AS chain, length(path) AS hops
ORDER BY hops DESC;
```

## Supply question — recombinant makers HQ'd within a region

```cypher
MATCH (c:Company)-[:HEADQUARTERED_IN]->(:Region)-[:PART_OF*0..2]->(:Region {name: $region})
MATCH (c)-[:MANUFACTURES]->(p:Product)
WHERE p:rFC OR p:rCR
RETURN c.name AS company, collect(DISTINCT p.name) AS products
ORDER BY company;
// params: { region: 'Europe' }
```

## Data-quality sweep — surface unverified facts

```cypher
MATCH (n)
WHERE n.notes CONTAINS 'VERIFY'
RETURN labels(n)[0] AS label, coalesce(n.name, n.number, n.id) AS node, n.notes
ORDER BY label;
```

## Whole-graph meta-model (run in Browser)

```cypher
CALL db.schema.visualization();
```
