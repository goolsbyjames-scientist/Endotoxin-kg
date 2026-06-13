# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A **learning sandbox** for knowledge graphs on Neo4j (Cypher) + Python. The
owner's goal is to understand how graphs work hands-on, so **clarity and
teaching value outweigh cleverness**. Code and Cypher are heavily commented on
purpose — preserve that style when editing, and explain graph concepts inline
rather than assuming familiarity.

The graph runs on **Neo4j Aura (free cloud tier)**, not a local server — there
is no Docker, Java, or Neo4j install on this machine (only Python 3.12). Do not
add a `docker-compose.yml` or assume a local Bolt server unless the owner
switches runtimes.

## The data: Bacterial Endotoxins Testing (BET)

The Aura database already contained a real domain graph when we connected (it
was **not** created by this project). It models the pharma QC field of endotoxin
testing and the transition from animal-derived **LAL** to **recombinant**
reagents (**rFC**, **rCR**).

Key modeling facts to know before writing queries:

- **Multi-labeled product nodes:** every product is `:Product` **and**
  `:Reagent` **and** one chemistry label — `:LAL` (17), `:rFC` (5), `:rCR` (6),
  or `:Bacteriophage` (1). Filter chemistry with `WHERE p:rFC OR p:rCR`, not a
  property.
- **Business key is `id`** on most nodes (e.g. `COMP_LONZA`, `PROD_LZ_KQCL`,
  `PAT_...`, `COMP_USP_86`); `name` is the human label. `:CompendialMethod` and
  `:Patent` use `name`/`number` as their readable identifier.
- **CompendialMethod recognition** is encoded as boolean properties:
  `recognizes_LAL`, `recognizes_rFC`, `recognizes_rCR`, `recognizes_MAT`,
  `recognizes_RPT`.
- **Region hierarchy:** `(:Region)-[:PART_OF]->(:Region)` (country → continent).
  Use `[:PART_OF*0..2]` to include sub-regions.
- Relationship types: `MANUFACTURES`, `HEADQUARTERED_IN`, `HAS_PRESENCE_IN`,
  `OWNS_PATENT`, `PROTECTS`, `ACQUIRED`, `OWNS`, `IN_FORCE_IN`,
  `HARMONIZED_WITH`, `PART_OF`.

**This is the owner's data — treat it as read-only by default.** Do not delete,
relabel, or restructure existing nodes without explicit confirmation. Some nodes
carry `notes` like `[VERIFY ...]`; don't silently "fix" domain facts.

## Commands

Run Python as modules **from the project root** (`C:\ClaudeCode`) with the venv
active. The driver reads credentials from `.env`.

```powershell
.\.venv\Scripts\Activate.ps1                  # activate venv (PowerShell)
python -m kg.connection                        # verify Aura connectivity
python -m kg.explore                           # introspect the live graph (labels/schema/samples)
python -m kg.query                             # run the domain example queries
python -m kg.load cypher/<file>.cypher         # run a .cypher file statement-by-statement
python -m kg.load                              # (no args) list runnable .cypher files
pip install -r requirements.txt                # install/refresh dependencies
```

`cypher/examples.cypher` is meant to be pasted into **Neo4j Browser** (Aura →
Open), not run by `kg.load` (it contains `CALL db.schema.visualization()` and
graph-drawing queries that only make sense in the Browser).

There is **no test suite or linter** configured. If adding tests, `pytest` is
the expected choice; keep them read-only against the shared Aura DB, or target a
throwayay instance.

## Architecture

Two surfaces over the same graph — reached visually (Browser) and
programmatically (Python):

- **`kg/connection.py`** is the **only** place that reads credentials (from
  `.env`) and builds the driver. Everything imports `get_driver()` /
  `get_database()` from here — keep it that way. It also forces UTF-8 on
  stdout/stderr because Windows' default cp1252 console crashes when printing
  scientific text from the data (Greek letters, arrows, °, ≥).
- **`kg/explore.py`** is a generic introspection tool (works on any Neo4j DB):
  label counts, label-set combinations, relationship types, the
  `(src)-[:REL]->(dst)` schema, and sample nodes per label. This is the right
  first step when handed an unfamiliar graph.
- **`kg/query.py`** holds the domain example queries and demonstrates
  `driver.execute_query(...)` plus **parameterized** queries.
- **`kg/load.py`** is a generic `.cypher` file runner: strips `//` comments,
  splits on `;`, runs each statement, and prints the change counters. The naive
  splitter assumes no `;` inside string literals (true for current files).

### Conventions that matter

- **Always parameterize** values from Python (`$name`). Property *keys* and
  *labels* can't be parameterized — if you must interpolate one, whitelist it
  (see `methods_recognizing` in `query.py`), never pass raw input.
- **Match the teaching tone:** new queries should be explained, and prefer the
  clearest Cypher over the most compact.
- When adding example queries, add them to **both** `cypher/examples.cypher`
  (for the Browser) and, if useful programmatically, `kg/query.py`.

## Secrets

`.env` holds the live Aura URI + password and is git-ignored. `.env.example` is
the committed template. Never write real credentials into any committed file.
