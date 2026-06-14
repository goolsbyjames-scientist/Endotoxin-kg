# Schema design: a scientific-claims knowledge graph

> **Status:** design draft, not yet implemented. This document captures the
> architecture we converged on for ingesting unstructured documents (open-access
> papers, patents, regulatory docs) into a queryable, standards-aligned knowledge
> graph that *extends* the existing Bacterial Endotoxins Testing (BET) graph.
>
> It is a **learning exercise**: the goal is to understand how a graph like the
> one already in Aura gets *built* from raw documents — so clarity and teaching
> value outweigh cleverness, same as the rest of this project.

---

## 1. Goal

Turn unstructured reports into structured data that can answer real
scientific/business questions — starting with a **queryable knowledge graph +
semantic search**, with predictive/decision models layered on later.

The project already has the **consumption half** of this pipeline:

- [`kg/embeddings.py`](../kg/embeddings.py) — embeds nodes, builds vector indexes
- [`kg/rag.py`](../kg/rag.py) — hybrid vector + graph + Claude search

What's missing is the **production half**: anything that turns a *document* into
*nodes*. This design fills that gap, slotting in upstream of `embeddings.py`:

```
documents -> ingest -> extract -> load -> (existing embeddings) -> (existing RAG)
```

---

## 2. The central idea: `Claim` is a first-class node

Documents do **not** link to each other directly. "This patent contrasts that
article" has a hidden question in it — *contrasts about what?* Two documents
usually agree on one point and diverge on another.

So every relationship routes **through a claim**. Documents each take a *stance*
on a shared claim:

```
(:Document)-[:ASSERTS {stance, confidence, quote}]->(:Claim)
```

`stance` in `supports | refutes | qualifies | neutral`. Now "patent contrasts
article" is a **derived** result (they assert the same claim with opposite
stances) — you *query* it, you don't store it. This is the structure used by
nanopublications and scientific argumentation graphs.

### Two tiers of claim

- **Atomic claim** — data-backed, falsifiable. *"Fluorescence rFC assay
  LoD = 0.001 EU/mL in buffer."* Has a number, a method, a source.
- **Narrative claim** — contested, perspective-dependent. *"Absorbance is better
  than fluorescence for signal detection."*

A narrative claim **decomposes into** atomic claims, each holding **under a
condition** — so it never gets a global truth value, only *conditioned*
verdicts:

```
(:NarrativeClaim "absorbance > fluorescence")
   -[:DECOMPOSES_TO {under:'low-cost / simple instrumentation'}]-> (:AtomicClaim "absorbance needs no fluorometer")
   -[:DECOMPOSES_TO {under:'low-concentration detection'}]->       (:AtomicClaim "fluorescence LoD 10x lower")
   -[:DECOMPOSES_TO {under:'turbid / colored sample matrix'}]->    (:AtomicClaim "absorbance suffers optical interference")
```

### Most claims are comparative, not absolute

The first real walkthrough (Mizumura et al. 2017 — see section 10) showed the
*dominant* claim shape in an experimental paper is **"A vs B under condition
C"**, not a standalone "X is true." Almost every result compared four
preparations of factor C (natural CTAL vs recombinant CCHO / CHEK / CSF) across
glycosylation, drug interference, and sensitivity. Two consequences:

- The compared subjects are **`:Preparation` (material) nodes** — the spine of
  the paper. A claim links to what it compares:
  `(:Claim)-[:COMPARES]->(:Preparation)`, and
  `(:Preparation)-[:PRODUCED_BY]->(:Method)`. Without this, comparative claims
  have nothing to compare *between* and collapse into mush.
- The clean numeric atomic claim (`LoD = 0.001 EU/mL`) is the **rare** case;
  most atomic findings are *qualitative-comparative* ("much greater", "steeper
  slope", "no binding"). Atomic claims must allow a null numeric value — the
  atomic/narrative split is a gradient, not a wall.

### "It depends" is resolved, not stored

The graph does not store a verdict for a perspective-dependent question. It
stores the **conditions** each piece of evidence is valid under, then resolves
against the user's needs:

1. **Filter / match** — keep evidence whose `:Condition`s overlap the user's
   profile (drop "for turbid water" evidence if the user tests clear buffers).
2. **Weight & aggregate** — score each option per criterion, weighted by the
   user's *priorities* (their weights) and by *evidence quality* (study type,
   recency, provenance, and **independence / conflict-of-interest**). The COI
   signal is *derivable from the graph itself* — if an authoring `:Institution`
   also `MANUFACTURES` the `:Product` a claim favours, the evidence is
   vendor-sourced and should be down-weighted.

Same graph, different user profile -> opposite answer, each fully sourced. The
**weighting scheme is an explicit modeling decision** — making it visible is the
whole point of doing this on a graph instead of in an LLM's gut feel.

---

## 3. Reified evidence (the nanopublication pattern)

To let a *condition* hang off an assertion, the assertion becomes a node, not a
bare edge:

```
(:Document)-[:REPORTS]->(:Evidence {confidence})
(:Evidence)-[:SUPPORTS|:REFUTES|:QUALIFIES]->(:Claim)
(:Evidence)-[:UNDER]->(:Condition {dimension:'application', value:'protein therapeutics'})
(:Evidence)-[:UNDER]->(:Condition {dimension:'priority',    value:'sensitivity'})
```

Each `:Evidence` node carries the *context window in which it is valid*. Those
`:Condition` dimensions are the hooks the user's needs grab onto at query time.
Evidence is pinned to the **specific experiment** (figure/table) it came from,
not just the document — one paper yields many evidence nodes (the 1/2/3-enzyme
assay alone produced three), and provenance must tell them apart.

---

## 4. The annotated schema (with standard ontology mappings)

We **borrow vocabulary and identifiers** from proven ontologies rather than
importing full OWL ontologies (which would bury the lesson). The reified-evidence
core is, by construction, the **nanopublication** pattern.

### Ontology legend

| Abbrev | Full name | Role |
|--------|-----------|------|
| **CiTO** | Citation Typing Ontology (SPAR) | typed document<->document stance |
| **FaBiO** | FRBR-aligned Bibliographic Ontology (SPAR) | document types |
| **PRO** | Publishing Roles Ontology (SPAR) | author roles |
| **PROV-O** | W3C Provenance Ontology | who/what/when extracted a fact |
| **SEPIO** | Scientific Evidence & Provenance Info Ontology | assertion <-> evidence <-> claim |
| **ECO** | Evidence & Conclusion Ontology | *type* of evidence (for weighting) |
| **schema.org** | schema.org `Claim`/`ClaimReview` | lightweight claim + rating |
| **OBI** | Ontology for Biomedical Investigations (OBO) | assays / methods |
| **UO** | Units of measurement Ontology (OBO) | units on measured values |
| **ChEBI / NCBITaxon** | OBO chemical / taxonomy | reagents / organisms |
| **EFO** | Experimental Factor Ontology | condition dimensions |
| **ORCID / ROR / DOI** | identifier registries | author / institution / document identity |

### Diagram

```
                    +---------------------------------------------+
                    |  PROVENANCE WRAPPER  (PROV-O / nanopub)      |
                    |  every :Evidence + :Claim node carries:      |
                    |   -[:WAS_DERIVED_FROM]-> :Document           |  prov:wasDerivedFrom
                    |   -[:WAS_GENERATED_BY]-> :ExtractionActivity |  prov:wasGeneratedBy
                    |   :ExtractionActivity {agent, model, ts,     |  prov:Activity + prov:Agent
                    |       confidence, status:'[VERIFY]'}         |
                    +---------------------------------------------+

   :Author                                                        :Institution
   foaf:Person / prov:Agent                                       org:Organization
   key = ORCID                                                    key = ROR
      |                                                              ^
      | [:AUTHORED]  (pro:author / dcterms:creator)                 | [:AFFILIATED_WITH]
      v                                                              |  org:memberOf
   +--------------------------+                                      |
   | :Document                |--------------------------------------+
   |  (+:Article/:Patent/     |
   |     :Regulatory)         |     [:CITES {type}]  ----------->  :Document
   |  fabio:JournalArticle /  |     CiTO: cito:supports,
   |  fabio:Patent /          |           cito:disagreesWith,
   |  fabio:Standard          |           cito:citesAsEvidence,
   |  key = DOI / PMID / patno|           cito:extends, cito:refutes
   +--------------------------+
        | [:USES_METHOD]            | [:ABOUT]                | [:REPORTS]
        |  OBI                      | dcterms:subject         | (asserts an evidence line)
        v                          v                          v
   :Method                    :Product / :Company        +------------------------+
   OBI:assay                  (EXISTING BET GRAPH)        | :Evidence  (reified)   |
   key = OBI id               link via MATCH, never       |  nanopub:assertion     |
   e.g. absorbance vs            relabel                  |  + ECO evidence type   |
        fluorescence assay                                |  {value, unit}  <- UO  |
                                                          +------------------------+
                                                            | [:UNDER]        | [:SUPPORTS |
                                                            |  EFO factor     |  :REFUTES |
                                                            v                 |  :QUALIFIES]
                                                       :Condition             |  SEPIO: supported-by
                                                       {dimension, value}     |       / weakened-by
                                                       EFO / OBI              v
                                                       (controlled vocab)   +----------------------+
                                                                            | :Claim               |
                                                                            | (+:AtomicClaim /     |
                                                                            |    :NarrativeClaim)  |
                                                                            | schema:Claim /       |
                                                                            | SEPIO assertion      |
                                                                            +----------------------+
                                                                              |           ^
                                          [:DECOMPOSES_TO {under}] -----------+           |
                                          (NarrativeClaim -> AtomicClaim)                 |
                                                                                          |
                                          [:CONTRADICTS | :REFINES] ----------------------+
                                          AIF / SEPIO  (claim <-> claim)
```

### Node mapping

| Our label | Standard class | Identity key | Notes |
|-----------|----------------|--------------|-------|
| `:Document` `:Article`/`:Patent`/`:Regulatory` | `fabio:JournalArticle` / `fabio:Patent` / `fabio:Standard` | DOI, PMID, patent no. | multi-label, like `:Product` |
| `:Claim` `:AtomicClaim`/`:NarrativeClaim` | `schema:Claim` / SEPIO assertion | normalized-text hash | two-tier split is **our extension** |
| `:Evidence` | nanopublication *assertion* + `ECO` type | surrogate id | reified hub; value+unit via `UO` |
| `:Author` | `foaf:Person` / `prov:Agent` | **ORCID** | ORCID solves most author entity-resolution |
| `:Institution` | `org:Organization` | **ROR** | ROR likewise for institutions |
| `:Method` | `obi:assay` | OBI id | absorbance vs fluorescence assays |
| `:Preparation` (material / reagent variant) | `obi:` material entity | surrogate id | the **comparison spine** (e.g. CTAL/CCHO/CHEK/CSF); `PRODUCED_BY` a `:Method` |
| `:Condition` | `EFO` experimental factor | dimension+value | controlled-vocab dimensions (our design) |
| `:ExtractionActivity` | `prov:Activity` (+ `prov:Agent`) | surrogate id | model, timestamp, confidence, `[VERIFY]` |
| `:Product`/`:Company`/`:CompendialMethod`/`:Region` | *existing BET graph* | `id`/`name` | link via `MATCH`, never relabel |

### Edge mapping

| Our edge | Standard property | From -> To |
|----------|-------------------|-----------|
| `[:AUTHORED {affiliation}]` | `pro:author` / `dcterms:creator` | `:Author` -> `:Document` — affiliation on the **edge** (document-bound, not a timeless author fact) |
| `[:AFFILIATED_WITH]` | `org:memberOf` | `:Author` -> `:Institution` (qualified per authoring document) |
| `[:CITES {type}]` | **CiTO** (`cito:supports`, `cito:disagreesWith`, `cito:citesAsEvidence`, `cito:extends`, `cito:refutes`) | `:Document` -> `:Document` |
| `[:REPORTS]` | nanopub assertion / `prov:wasGeneratedBy` (inverse) | `:Document` -> `:Evidence` |
| `[:SUPPORTS]`/`[:REFUTES]`/`[:QUALIFIES]` | **SEPIO** supported-by / weakened-by | `:Evidence` -> `:Claim` |
| `[:UNDER]` | `EFO`/`OBI` factor | `:Evidence` -> `:Condition` |
| `[:USES_METHOD]` | `obi:` | `:Document` -> `:Method` |
| `[:PRODUCED_BY]` | `obi:` / nanopub | `:Preparation` -> `:Method` |
| `[:COMPARES]` | *our extension* | `:Claim` -> `:Preparation` / `:Method` / `:Product` |
| `[:ABOUT]` | `dcterms:subject` | `:Document` -> `:Product`/`:Company` |
| `[:CONTRADICTS]`/`[:REFINES]` | AIF / SEPIO claim relations | `:Claim` -> `:Claim` |
| `[:DECOMPOSES_TO {under}]` | *our extension* (closest: micropublication) | `:NarrativeClaim` -> `:AtomicClaim` |
| `[:WAS_DERIVED_FROM]` | `prov:wasDerivedFrom` | `:Evidence`/`:Claim` -> `:Document` |
| `[:WAS_GENERATED_BY]` | `prov:wasGeneratedBy` | `:Evidence`/`:Claim` -> `:ExtractionActivity` |

---

## 5. Agent architecture: one agent, several skills, multi-agent only for verification

Three different primitives, used for three different jobs:

- **Tools** = the agent's hands: `fetch_document`, `search_graph`,
  `find_similar_claim` (embeddings), `write_node`. Shared by everything.
- **Skills** = loadable instruction packs the *same* agent pulls in per document
  type. This is the right tool for "handle different document types": a patent
  (assignees, inventors, priority dates, numbered claims) is nothing like a
  journal article (abstract, methods, results, refs). Build:
  `extract-article`, `extract-patent`, `extract-regulatory`. **You do not need
  separate agents per document type.**
- **Subagents (multi-agent)** = separate context windows. Worth it for only two
  things, and both *later*:
  1. **Parallel throughput** when batch-processing many documents.
  2. **Adversarial verification** — an independent agent that challenges a stance
     assignment ("you said *supports*; argue it's *refutes* or *qualifies*").
     A claims graph lives or dies on stance accuracy, so this is the one place
     multi-agent genuinely pays off.

**Build order:** single orchestrator agent + doc-type skills + small tool set
first; add the adversarial verifier subagent once single-agent extraction works.
Starting multi-agent means debugging orchestration before understanding
extraction — backwards for learning.

**Each extraction skill must be an exhaustive checklist, not a "summarize"
prompt.** The first walkthrough (section 10) under-extracted badly when prompted
for "the gist": it captured ~6 claims where a section-by-section pass found ~16.
The skill must force per-section sweeps ("extract *every* method, *every*
measured result; quote and quantify"), and a **completeness-critic** pass should
ask "which figures/tables produced no claim?" before a document is accepted.

> When we implement this, confirm the exact skill / subagent / tool mechanics
> against the Claude Agent SDK reference rather than assuming — the *concepts*
> here are stable, the API specifics should be verified.

---

## 6. Guardrails (these are also the real lessons)

1. **Existing BET data is read-only.** Extracted facts go into *new* labels
   (`:Document`, `:Claim`, `:Evidence`, ...), linked to existing nodes via
   `MATCH`, never relabeling or overwriting them. Keeps machine-extracted data
   quarantined from curated data.
2. **Provenance on every fact.** Each node/relationship carries its source
   (PMID/DOI) and a confidence, via the PROV-O wrapper. Follow the existing
   `[VERIFY ...]` `notes` convention so extracted facts are visibly "not yet
   trusted."
3. **Entity resolution proposes, never auto-merges.** Matching extracted
   "Lonza" to existing `COMP_LONZA` is the hard part; getting it wrong silently
   corrupts the graph. Use embeddings for candidate matching, human (or the
   adversarial agent) confirms borderline cases.

---

## 7. The hard parts (where the time goes)

1. **Claim normalization / dedup — hardest.** When are two sentences the same
   claim? Entity resolution but for *sentences*. Embeddings find candidates; a
   human/agent confirms. Get it wrong -> graph fragments or over-merges.
2. **Stance detection** — supports/refutes/qualifies is subtle, especially
   "qualifies" ("equivalent *only for gram-negative* endotoxins"). Guarded by
   the verifier subagent.
3. **Entity resolution to the existing graph** — propose, don't auto-merge;
   provenance on everything.
4. **Extraction completeness** — a single "summarize" pass returns highlights,
   not an inventory. Exhaustive extraction needs section-by-section sweeps + a
   completeness critic (see section 10). This was *the* lesson from the first
   walkthrough.

---

## 8. Open decisions

- **Condition dimensions:** controlled vocabulary for dimension *names*
  (application, matrix, priority, regime), free-ish values tagged with EFO/OBI
  IDs where they exist. (Leaning controlled-vocab.)
- **User-needs model:** structured intake (dropdowns -> deterministic
  resolution, teaches the decision model cleanly) vs free-text parsed by the
  agent (more natural, fuzzier to debug).
- **Claim granularity:** keep both atomic and narrative tiers; confirm the
  `DECOMPOSES_TO {under}` shape survives contact with a real paper.
- **Crawl scope:** autonomous citation-frontier crawling vs approve-each-document
  ingestion (safer for the shared Aura DB).

Settled by the first walkthrough (section 10), now part of the design:

- **`:Preparation` node added** as the comparison spine, with
  `(:Claim)-[:COMPARES]->(:Preparation)-[:PRODUCED_BY]->(:Method)`.
- **Authorship reified:** affiliation lives on the `[:AUTHORED]` edge
  (document-bound).
- **COI as a quality weight,** derived from author -> institution ->
  manufactured-product links.
- **Atomic claims may be non-numeric** (qualitative-comparative); atomic vs
  narrative is a gradient.
- **Evidence provenance to the experiment** (figure/table), not just the paper.

---

## 9. Proposed module layout (not yet built)

| Stage | Module | Responsibility |
|-------|--------|----------------|
| Ingest | `kg/ingest.py` | fetch open-access full text (Europe PMC REST API, free, no key), cache raw to `data/raw/` |
| Extract | `kg/extract.py` | hand Claude a target schema, get typed JSON: `:Document` + claims + evidence + conditions, with provenance |
| Load | extend [`kg/load.py`](../kg/load.py) | `MERGE` new nodes; link to existing nodes via `MATCH` |
| (reuse) | [`kg/embeddings.py`](../kg/embeddings.py) | extends ~5 lines to embed `:Claim`/`:Document` |
| (reuse) | [`kg/rag.py`](../kg/rag.py) | searches the new nodes for free |

**First step:** one paper, end to end, by hand — fetch, extract to JSON, eyeball
against the graph, load a single `:Document` node — before automating anything.
A vertical slice exposes where the pipeline is fragile (always stages
3-4: extraction + entity/claim resolution) without polluting the shared Aura DB.

---

## 10. First walkthrough — Mizumura et al. 2017 (rCR), and what it changed

**Test document:** Mizumura H, Ogura N, Aketagawa J, et al. "Genetic engineering
approach to develop next-generation reagents for endotoxin quantification."
*Innate Immunity* 23(2):136-146, 2017. DOI 10.1177/1753425916681074,
PMID 27913792, open access (PMC5302069). Seikagaku Corporation's foundational
recombinant cascade reagent (rCR) paper — chosen because it is comparative and
manufacturer-authored, stressing both the claim model and provenance.

**The extraction-completeness lesson (the big one).** A first "give me the gist"
pass produced 4 methods and ~6 claims. Reading the Methods and Results section by
section produced **11 methods and ~16 atomic claims** — the three expression
systems (baculovirus-transient / stable Sf9 / CHO DG44 / HEK293), Western-blot
molecular-weight ordering, the 1/2/3-enzyme protease-activity series, the lectin
glycosylation panel (Con A / LCA / MAM / SSA), and the drug-interference panel.
The fix was not a better model; it was changing the instruction from *summarize*
to *list every experiment and result, quote and quantify*. Hence the
checklist-driven skill + completeness critic in section 5.

**Refinements adopted into the schema (sections 2-5, 7-8):**

1. **`:Preparation` material node** — the comparison spine (CTAL/CCHO/CHEK/CSF),
   `PRODUCED_BY` a method, `COMPARES`d by claims.
2. **Comparative-conditioned claim is the norm,** not the exception — "A vs B
   under C". The standalone numeric atomic claim is rare.
3. **Atomic claims may be qualitative** (no number): "steeper slope", "no
   binding".
4. **Authorship reified** — affiliation on the `[:AUTHORED]` edge (Kawabata was
   at Kyushu University, the rest at Seikagaku; affiliation is document-bound).
5. **Conflict-of-interest signal** — 6 of 7 authors were Seikagaku employees and
   the paper favours Seikagaku's own product; derive independence from
   author -> institution -> product links and down-weight vendor-sourced
   evidence.
6. **Evidence provenance to the specific experiment** (figure/table), not just
   the document.

**Entity-resolution decisions surfaced (not yet run live):** "Seikagaku
Corporation" should resolve to an existing `:Company` node, the rCR product to
existing `:rCR` nodes, and the natural lysate "Endospecy ES-50M" to an existing
`:LAL` product; "Kyushu University" is a new `:Institution` (resolve via ROR);
author ORCIDs were absent and would be flagged low-confidence. Two
discussion-level claims (no factor G -> no beta-glucan false positives; no
coagulogen competition) carry lower confidence + `[VERIFY]`.
</content>
</invoke>
