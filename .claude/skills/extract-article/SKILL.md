---
name: extract-article
description: Exhaustively extract ONE peer-reviewed scientific article into the claims knowledge-graph schema (Document, Preparations, Methods, atomic/narrative Claims, Evidence, Conditions, Citations) with provenance. Use when ingesting a journal paper (PMID / DOI / PMC URL) into the BET knowledge graph.
allowed-tools: Read, WebFetch, WebSearch, Grep, Glob, Write
---

# Extract a scientific article into the claims graph

You convert ONE peer-reviewed article into structured JSON that conforms to the
project's claims-graph schema (full design: [schema-design.md](../../../docs/schema-design.md)).
You perform the **extract** stage only — you do NOT resolve entities against the
live Neo4j graph and you do NOT write Cypher (that is the separate load step).

## Prime directive: be exhaustive, not a summarizer

A "gist" pass is a FAILURE. Every method, every measured result, and every
comparison is a candidate claim. This skill exists because a summarize-style pass
on the reference paper found ~6 claims where a section-by-section pass found ~16.
If your output reads like an abstract, you have done it wrong.

## Procedure

### 1. Ingest — get the full text
Input may be a URL or a local PDF. Either way, capture DOI / PMID / title /
venue / year / pages, and never work from the abstract alone.
- **URL** (prefer PMC open access): fetch the FULL TEXT — Methods and Results
  especially.
- **Local PDF** (e.g. `data/raw/<name>.pdf`): read it as **page images** so you
  also capture **figure/table data** (homology %, sizes, slopes, EU/mL) that a
  text layer misses. Try the Read tool with the `pages` parameter first; on
  Windows the Read tool's PDF path may fail (no poppler/pdftoppm installed) — if
  so, render with PyMuPDF (a project dependency) and read the PNGs:
  `python -c "import fitz; d=fitz.open(r'<pdf>'); [p.get_pixmap(dpi=150).save(rf'data/raw/_tmp_{{i}}.png') for i,p in enumerate(d)]"`
  then Read the PNGs (delete them after). Capture figure numbers instead of
  marking `data_in_figure_only`; set that flag only when a value truly can't be
  read even from the image.

### 2. Exhaustive sweep — section by section
Walk the paper IN ORDER. For EACH section, extract everything; do not stop at the
headline findings. Tick every box:

- [ ] **Bibliographic** — title, venue, year, DOI / PMID / PMC.
- [ ] **Authors** (in order) + each author's affiliation **as stated in this
      paper** (affiliation is document-bound, not a global fact).
- [ ] **Institutions** — name + city/country.
- [ ] **Methods / assays** — every distinct technique with its key parameters
      (instrument, substrate, wavelength, vectors, cell lines, buffers, units).
      Expect MANY (expression systems, blots, activity assays, glycosylation
      panels, interference tests, sensitivity curves...).
- [ ] **Preparations / materials** — every named variant that is COMPARED across
      experiments (e.g. the same protein from different cell lines). These are
      the **comparison spine**; record each name and abbreviation, and which
      `:Method` produced it.
- [ ] **Atomic claims** — every measured/observed result. Most are *comparative*
      ("A vs B") and *conditioned* ("under C"), and many are *qualitative*
      ("steeper slope", "no binding") with NO number — capture those too. Record
      value + unit when present.
- [ ] **Narrative claims** — the paper's higher-level "X is better / viable"
      statements; link each to the atomic claims that support it.
- [ ] **Conditions** — the context each result holds under (matrix, priority,
      readout, specificity, time-point, ...).
- [ ] **Citations / leads** — key references and HOW each is used
      (authority / uses-method / supports / disagrees-with).

### 3. Structure the output
Emit ONE JSON object (schema below). For every claim include: a `quote` from the
paper, the `:Preparation`/`:Method` it `compares`, the `under` condition(s), a
`stance`, and a `confidence` (0-1). Mark claims drawn from the Discussion (not
the Results) with `"verify": true` and a lower confidence.

### 4. Completeness self-check — REQUIRED before finishing
Re-read EVERY figure and table. For each one, name the claim(s) it produced. If
any figure or table produced zero claims, go back and extract it — a figure with
no claim is almost always a miss. Then state the tally:
`methods=N, preparations=N, atomic=N, narrative=N` and confirm no figure/table is
unaccounted for.

### 5. Provenance + handoff
- Stamp every claim with the source id, its `evidence_figure`, and a default
  `[VERIFY]` status.
- Note entity-resolution **candidates** (companies / products / institutions that
  may already exist in the BET graph) but DO NOT merge them — flag for the load
  step.
- Recommend that the main agent next invoke the **verify-extraction** subagent
  (fresh context, adversarial) to challenge stance assignments and completeness.

### Rules for tricky cases
- **Stance reflects THIS paper's evidence, not general truth.** `supports` /
  `refutes` require an experiment performed *in this article*. Discussion sections
  routinely list *theoretical advantages* / design rationale that were never
  tested (e.g. "lacks factor G, so no beta-glucan false positives"). Tag those
  `"basis": "theoretical"`, set stance `neutral`, and `verify: true`; only
  experimentally demonstrated findings get `"basis": "experimental"` plus a
  `supports`/`refutes` stance. When a paper enumerates an "advantages" list, check
  each item against whether a result actually backs it — usually most do not.
  Use `"basis": "computational"` for analytical/derived results (sequence
  homology, hydropathy, structure prediction, in-silico folding): demonstrated,
  so `supports` is fine, but they are not wet-lab experiments. **Treat
  "unpublished data / patent pending" disclosures like a COI** — they cannot be
  scored as demonstrated here, so drop the confidence and set `verify: true`.
- **Figure-only numbers.** Full-text fetches return *text*, not figure images, so
  values that live only in a chart (bar heights, curve slopes, EU/mL ranges,
  per-drug percentages) cannot be read. Capture the claim qualitatively, set
  `"qualitative": true` and `"data_in_figure_only": true`, lower the confidence,
  and say so — never silently drop it.
- **Setup / normalization statements** ("we tuned conditions so all variants were
  equivalent at baseline") are method-setup, not results. Log as a `neutral`
  atomic claim only if a figure depicts them; otherwise fold into the relevant
  `:Method` params.
- **Evidence is collapsed into claims at this stage.** Do NOT emit separate
  `:Evidence` nodes — put the `quote`, `under` conditions, `confidence`, and
  `evidence_figure` on the claim. Evidence is reified into nodes only at the load
  step (see schema-design.md section 3).
- **Conflict of interest — capture it even when the paper denies it.** If authors
  are affiliated with the maker of a product the paper favours, record a
  `COI-weight` entry in `resolution_candidates` derived from
  author -> institution -> product, *even if the paper declares "no conflicts."*

## Output schema (compact)

```json
{
  "document": {
    "labels": [":Document", ":Article"],
    "doi": "", "pmid": "", "pmc": "",
    "title": "", "venue": "", "year": 0, "volume": "", "issue": "", "pages": "",
    "open_access": true,
    "fabio_type": "fabio:JournalArticle"
  },
  "authors": [
    {"name": "", "role": "author|corresponding", "orcid": null, "affiliation": ""}
  ],
  "institutions": [{"name": "", "ror": null, "city": ""}],
  "methods": [{"id": "M1", "name": "", "obi": null, "params": ""}],
  "preparations": [
    {"id": "P-CCHO", "name": "", "abbrev": "", "produced_by": "M3", "note": ""}
  ],
  "claims": [
    {
      "id": "AC1", "tier": "atomic|narrative",
      "text": "", "quote": "",
      "value": null, "unit": null, "qualitative": true,
      "compares": ["P-CCHO", "P-CSF"],
      "under": ["matrix:injectable drugs"],
      "stance": "supports|refutes|qualifies|neutral",
      "basis": "experimental|computational|theoretical|discussion",
      "decomposes_to": [],
      "evidence_figure": "Fig 3a", "data_in_figure_only": false,
      "confidence": 0.9, "verify": false
    }
  ],
  "conditions": [{"dimension": "", "value": ""}],
  "cites": [{"ref": "", "cito": "citesAsAuthority|usesMethodIn|supports|disagreesWith"}],
  "resolution_candidates": [
    {"extracted": "Seikagaku Corporation", "type": "Company", "maybe_existing": "COMP_SEIKAGAKU", "action": "MATCH-or-flag"},
    {"extracted": "COI: N of M authors employed by <product maker>", "type": "COI-weight", "maybe_existing": null, "action": "down-weight vendor-sourced evidence"}
  ],
  "completeness": {
    "methods": 0, "preparations": 0, "atomic": 0, "narrative": 0,
    "figures_accounted": {"Figure 1": "schematic - no measured claim", "Figure 2": "AC1, AC2"},
    "unaccounted_figures": []
  },
  "provenance": {
    "source_id": "PMC.../PMID.../DOI...",
    "default_status": "[VERIFY]",
    "extraction_stage": "extract-only (no live-graph resolution, no Cypher writes)",
    "recommended_next": "invoke verify-extraction subagent (fresh adversarial context)"
  }
}
```

## What you must NOT do
- Do not summarize or cherry-pick only the "important" findings.
- Do not resolve/merge entities into the live graph or run Cypher writes.
- Do not invent ORCIDs, RORs, or numeric values not in the source — leave them
  `null` and flag.
