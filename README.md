# Knowledge Graph Lab — Bacterial Endotoxins Testing

A hands-on project for **learning how knowledge graphs work** using
[Neo4j](https://neo4j.com/) and the Cypher query language. You explore one real
graph two ways:

- **Visually**, in the Neo4j Browser (point-and-click node/edge canvas).
- **Programmatically**, from Python using the official `neo4j` driver.

## The graph

The Aura database holds a real domain graph about **Bacterial Endotoxins
Testing (BET)** — the pharmaceutical QC field that keeps bacterial pyrogens out
of injectable drugs. It captures the industry's ongoing shift from the
traditional animal-derived **LAL** reagent (Limulus Amebocyte Lysate, from
horseshoe-crab blood) to **recombinant** reagents (**rFC** = recombinant Factor
C, **rCR** = recombinant Cascade Reagent), and the companies, patents,
pharmacopeia chapters, and regions involved.

```
~84 nodes, ~150 relationships

Labels                              Relationships
  :Product (+:Reagent +chemistry)     (:Company)-[:MANUFACTURES]->(:Product)
    chemistry ∈ :LAL :rFC :rCR        (:Company)-[:HEADQUARTERED_IN]->(:Region)
                :Bacteriophage        (:Company)-[:HAS_PRESENCE_IN]->(:Region)
  :Company                            (:Company)-[:OWNS_PATENT]->(:Patent)
  :Patent                             (:Company)-[:ACQUIRED|:OWNS]->(:Company)
  :CompendialMethod                   (:Patent)-[:PROTECTS]->(:Product)
  :Region                             (:CompendialMethod)-[:IN_FORCE_IN]->(:Region)
                                      (:CompendialMethod)-[:HARMONIZED_WITH]->(:CompendialMethod)
                                      (:Region)-[:PART_OF]->(:Region)
```

> **Note:** every `:Product` node also carries the `:Reagent` label *and* a
> chemistry label (`:LAL` / `:rFC` / `:rCR` / `:Bacteriophage`). Multi-labeling
> like this is a common knowledge-graph modeling pattern — see queries #2–3.

> **History:** this project began by seeding a tiny toy graph (`:Person` /
> `:Concept` / `:Topic`), then discovered the database already contained the BET
> graph above and pivoted to it. The toy nodes were removed via
> `cypher/remove_toy_seed.cypher`.

## What's here

```
cypher/
  examples.cypher          11 numbered, explained queries to paste into Neo4j Browser.
  remove_toy_seed.cypher   One-off cleanup that deleted the original toy nodes (kept for record).
kg/
  connection.py   Builds a Neo4j driver from .env; forces UTF-8 output on Windows.
  explore.py      Introspects ANY graph: labels, label-sets, relationships, schema, samples.
  query.py        Runs domain queries from Python (traversal, multi-label, paths, aggregation).
  load.py         Generic runner: executes a .cypher file statement-by-statement.
.env.example      Template for your connection secrets. Copy to .env.
requirements.txt  Python dependencies (neo4j, python-dotenv).
```

## Setup

### 1. Python environment (PowerShell, from `C:\ClaudeCode`)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Connect to your Neo4j Aura instance

```powershell
copy .env.example .env   # then edit .env with your URI + password
python -m kg.connection  # should print "Connected to Neo4j ..."
```

`.env` is git-ignored. Username is `neo4j`; the URI looks like
`neo4j+s://xxxx.databases.neo4j.io`.

## Explore

**Understand the shape first** (works on any graph):

```powershell
python -m kg.explore
```

**Run the domain queries from Python:**

```powershell
python -m kg.query
```

**See it drawn:** in the Aura console click **Open** to launch Neo4j Browser,
then paste queries from `cypher/examples.cypher` one at a time (`Ctrl+Enter`).
Start with #0 (`CALL db.schema.visualization()`) to see the meta-model, then #1.

## Concepts this project teaches

| Idea | Where to see it |
| --- | --- |
| Introspecting an unknown graph (labels, schema, samples) | `kg/explore.py` |
| Multi-label nodes (`:Product:Reagent:rFC`) | `examples.cypher` #2–3, `kg/query.py` |
| Pattern matching = a picture of the subgraph | `examples.cypher` #1, #5 |
| Chained traversal across node types | `examples.cypher` #5, #9 |
| Variable-length paths (`*1..n`) | `examples.cypher` #6, #8; acquisition chains in `query.py` |
| Shortest path | `examples.cypher` #7 |
| Aggregation & grouping | `examples.cypher` #2, `query.py` |
| Degree centrality | `examples.cypher` #10, `query.py` |
| Parameterized queries from code | `kg/query.py` |

## Things to try next

- **Ask the graph a question** of your own and write the Cypher for it — e.g.
  "which patents protecting recombinant products are already expired?"
- Add `:HARMONIZED_WITH` reasoning: which LAL methods are mutually recognized
  across regions?
- Pull query results into a notebook or an LLM prompt for retrieval-augmented
  answers about the endotoxin-testing landscape.
- If you want a *clean* sandbox to model your own domain from scratch, spin up a
  second Aura instance and point `.env` at it.

---

## 🆕 Hybrid RAG System

This project now includes a **Retrieval-Augmented Generation (RAG)** system that
makes the graph accessible via a web interface:

- **Vector Search** (`kg/embeddings.py`) — Embeds product/method descriptions
  using Sentence Transformers
- **Hybrid Search** (`kg/rag.py`) — Combines semantic vectors + graph traversal to
  answer domain questions
- **Web UI** (`app.py`) — Streamlit interface for searching products + regulatories
- **Online** — Deployable to Streamlit Cloud (free)

### Quick Start (RAG only)

```powershell
# Generate embeddings (first time)
python -m kg.embeddings

# Test RAG search from Python
python -m kg.rag

# Run web app locally
streamlit run app.py
```

See `DEPLOYMENT_README.md` for full deployment guide to Streamlit Cloud.
