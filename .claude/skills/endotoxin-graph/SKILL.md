---
name: endotoxin-graph
description: >
  Work with the Bacterial Endotoxins Testing (BET) knowledge graph in this
  project's Neo4j Aura database. Use when the user wants to query, explore,
  visualize, validate, or extend the graph, asks a domain question about
  endotoxin-testing products / companies / patents / compendial methods /
  regulatory documents / market segments / regions, or wants to write Cypher
  against it.
when_to_use: >
  Triggers: "query the graph", "what does the graph say about ...", "add this to
  the graph", "which companies make rFC", "run this Cypher", "explore the BET
  data", "endotoxin", "LAL vs recombinant".
argument-hint: [a question or Cypher to run]
allowed-tools: >
  Bash, Read, Glob, Grep,
  PowerShell(C:\ClaudeCode\.venv\Scripts\python.exe *)
---

# Endotoxin (BET) knowledge graph

A Neo4j Aura graph about **Bacterial Endotoxins Testing**: the pharma-QC field
covering the shift from animal-derived **LAL** to **recombinant** reagents
(**rFC**, **rCR**), plus the companies, patents, pharmacopeia chapters,
regulatory documents, market segments, and regions involved.

The Python package `kg/` (in the project root, `C:\ClaudeCode`) is the way in.
Run modules from the project root with the venv interpreter
`C:\ClaudeCode\.venv\Scripts\python.exe`.

## First, get current ground-truth

The graph changes, so don't trust a hardcoded schema. Refresh it:

```
python -m kg.explore --schema     # labels + relationships only (fast, compact)
python -m kg.explore              # + sample nodes per label
python -m kg.connection           # verify connectivity first if anything errors
```

A reference snapshot of the model lives in
[schema-snapshot.md](schema-snapshot.md) — read it for orientation, but prefer
`--schema` output as the source of truth.

## Conventions (follow these)

- **Read-only by default.** This is the owner's real data. Do NOT create,
  delete, relabel, or restructure nodes without explicit confirmation. Mutations
  go through a reviewed `cypher/*.cypher` file run via `python -m kg.load <file>`
  (idempotent `MERGE`), never ad-hoc deletes.
- **Multi-label products:** every product is `:Product:Reagent` plus a chemistry
  label `:LAL` / `:rFC` / `:rCR` / `:Bacteriophage`. Filter chemistry with a
  label test (`WHERE p:rFC OR p:rCR`), not a property.
- **Business key is `id`** (e.g. `COMP_LONZA`, `PROD_LZ_KQCL`); `name` is the
  human label. Patents use `number`, methods use `name`.
- **Respect `[VERIFY]` notes.** Some nodes carry `notes` flagging unverified
  facts — surface them, don't silently treat them as confirmed.
- **Parameterize** values from Python (`$name`); never string-format user input
  into Cypher. Labels/property-keys can't be parameters — whitelist if you must
  interpolate.

## How to answer a graph question

1. If the schema might matter, run `python -m kg.explore --schema` first.
2. Write Cypher; run it from Python via `kg/query.py` style
   (`driver.execute_query(cypher, **params, database_=get_database())`), or add
   a small function to `kg/query.py` if it's reusable.
3. For anything the user should *see*, give them the Cypher to paste into Neo4j
   Browser (Aura → Open) and note what it draws.

## Ready-made query recipes

Common patterns (recombinant adoption, patent expiry, regulatory references,
segment coverage, acquisition lineage) are in
[recipes.md](recipes.md) — read it when a question matches one of those shapes.

## Running one-off Cypher quickly

Prefer adding a named function to `kg/query.py`. For a true one-off, a short
inline script using `kg.connection.get_driver()` is fine — keep it read-only.
