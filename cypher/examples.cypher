// ============================================================================
// examples.cypher — guided queries over the Bacterial Endotoxins Testing graph
// ============================================================================
//
// Paste these one at a time into the Neo4j Browser query bar and press
// Ctrl+Enter. Queries that RETURN nodes/relationships are drawn as a graph;
// queries that return values show a table.
//
// THE DOMAIN (what the graph is about)
//   Bacterial endotoxins (pyrogens from Gram-negative bacteria) must be kept
//   out of injectable drugs and medical devices. They're detected with the
//   "Bacterial Endotoxins Test" (BET). Three reagent chemistries:
//     - LAL  : traditional Limulus Amebocyte Lysate (from horseshoe-crab blood)
//     - rFC  : recombinant Factor C        }  animal-free, the modern transition
//     - rCR  : recombinant Cascade Reagent }
//   The graph captures the PRODUCTS, the COMPANIES that make/own them, the
//   PATENTS protecting them, the COMPENDIAL METHODS (pharmacopeia chapters)
//   that recognize each chemistry, and the REGIONS where those methods apply.
//
// THE MODEL (run query #0 to see it live)
//   (:Company)-[:MANUFACTURES]->(:Product)        a Product is also :Reagent
//   (:Product) also carries a chemistry label: :LAL | :rFC | :rCR | :Bacteriophage
//   (:Company)-[:HEADQUARTERED_IN | :HAS_PRESENCE_IN]->(:Region)
//   (:Company)-[:OWNS_PATENT]->(:Patent)-[:PROTECTS]->(:Product)
//   (:Company)-[:ACQUIRED | :OWNS]->(:Company)
//   (:CompendialMethod)-[:IN_FORCE_IN]->(:Region)
//   (:CompendialMethod)-[:HARMONIZED_WITH]->(:CompendialMethod)
//   (:Region)-[:PART_OF]->(:Region)               country -> continent
// ----------------------------------------------------------------------------


// 0. THE LIVE SCHEMA. Neo4j introspects the graph and draws the meta-model:
//    which labels exist and how they connect. Best first thing to run.
CALL db.schema.visualization();


// 1. SEE A SLICE of the real data: companies and what they make.
MATCH (c:Company)-[m:MANUFACTURES]->(p:Product)
RETURN c, m, p
LIMIT 50;


// 2. THE RECOMBINANT TRANSITION. Which products are animal-free (rFC/rCR)
//    versus traditional LAL? `p:rFC OR p:rCR` tests for chemistry labels.
MATCH (c:Company)-[:MANUFACTURES]->(p:Product)
RETURN p.chemistry AS chemistry,
       count(*) AS products,
       collect(DISTINCT c.name)[..5] AS some_makers
ORDER BY products DESC;


// 3. WHO SELLS RECOMBINANT? Companies that make at least one rFC or rCR product
//    — i.e. who has moved beyond horseshoe-crab LAL.
MATCH (c:Company)-[:MANUFACTURES]->(p:Product)
WHERE p:rFC OR p:rCR
RETURN c.name AS company, collect(p.name) AS recombinant_products
ORDER BY company;


// 4. REGULATORY ACCEPTANCE. Which compendial methods recognize recombinant
//    reagents? This is the crux of the industry's animal-free transition.
MATCH (m:CompendialMethod)
WHERE m.recognizes_rFC OR m.recognizes_rCR
RETURN m.name AS method, m.title AS title,
       m.recognizes_rFC AS rFC, m.recognizes_rCR AS rCR, m.effective_year AS since
ORDER BY since;


// 5. PATENT LANDSCAPE. Who owns the patents, and what products do they protect?
//    (OWNS_PATENT and PROTECTS chained: Company -> Patent -> Product.)
MATCH (c:Company)-[:OWNS_PATENT]->(pat:Patent)-[:PROTECTS]->(prod:Product)
RETURN c.name AS owner, pat.number AS patent, pat.status AS status,
       pat.expiration_year AS expires, collect(DISTINCT prod.name) AS protects
ORDER BY expires;


// 6. CORPORATE LINEAGE (variable-length path). Follow ACQUIRED chains to see
//    how today's companies absorbed older ones. *1..5 = 1 to 5 hops.
MATCH path = (acquirer:Company)-[:ACQUIRED*1..5]->(absorbed:Company)
RETURN path;


// 7. SHORTEST PATH between two companies through any relationships — how are
//    Lonza and bioMérieux connected in this graph at all?
MATCH (a:Company {name: 'Lonza'}), (b:Company {name: 'bioMérieux'})
MATCH path = shortestPath((a)-[*..6]-(b))
RETURN path;


// 8. REACH ACROSS HOPS. Which regions can each compendial method's recognition
//    reach, including sub-regions? Method -> Region <- (countries PART_OF it).
//    Shows variable-length traversal *over the region hierarchy*.
MATCH (m:CompendialMethod {name: 'USP <86>'})-[:IN_FORCE_IN]->(r:Region)
OPTIONAL MATCH (child:Region)-[:PART_OF*1..2]->(r)
RETURN m.name AS method, r.name AS in_force_region,
       collect(DISTINCT child.name) AS includes_subregions;


// 9. A SUPPLY QUESTION the graph answers in one pattern:
//    "Which companies headquartered in Europe make a recombinant assay?"
//    Joins MANUFACTURES + chemistry label + region hierarchy.
MATCH (c:Company)-[:HEADQUARTERED_IN]->(:Region)-[:PART_OF*0..2]->(:Region {name: 'Europe'})
MATCH (c)-[:MANUFACTURES]->(p:Product)
WHERE p:rFC OR p:rCR
RETURN c.name AS european_company, collect(DISTINCT p.name) AS recombinant_products;


// 10. DEGREE CENTRALITY. The most-connected nodes — usually the hub companies
//     and the products everything references.
MATCH (n)
RETURN coalesce(n.name, n.number, n.id) AS name, labels(n) AS labels,
       count { (n)--() } AS degree
ORDER BY degree DESC
LIMIT 10;
