---
name: ingest-extraction
description: Take a VERIFIED extraction JSON through the human review gate and then run the hands-off load -> embed -> snapshot pipeline into the BET knowledge graph. Use after extract-article + verify-extraction have produced a reconciled extraction and the user wants to land it in the graph.
allowed-tools: Read, Edit, PowerShell(C:\ClaudeCode\.venv\Scripts\python.exe *)
---

# Ingest a verified extraction into the graph

The ONLY human-judgment step is reviewing the extraction against the paper.
Everything after approval is logistical and runs hands-off.

## 1. Human review gate (the one judgment step)

Generate the readable review:

```
C:\ClaudeCode\.venv\Scripts\python.exe -m kg.review <extraction.json>
```

This writes `<extraction>_review.md` and floats the verifier's flags (theoretical
claims, figure-only data, low-confidence, conflict of interest) to the top. Show
the user those priorities and ask them to check the methods / claims / stances
against the paper.

**Corrections are conversational.** When the user says what is wrong (e.g. "AC4
stance should be neutral", "drop NC7", "AC12 quote is mismatched"), edit the gold
JSON with the Edit tool, then re-run `kg.review` and show what changed. Repeat
until the user explicitly approves.

## 2. Hands-off pipeline (only after explicit approval)

Run once:

```
C:\ClaudeCode\.venv\Scripts\python.exe -m kg.pipeline <extraction.json> --commit
```

This loads the nodes, MATCH-links them to curated nodes (auto-writing links and
tagging low-confidence ones `[VERIFY]`), embeds the new `:Claim` / `:Document`
nodes, and regenerates the schema snapshot. Report the change counts.

## Rules

- **Never** run the pipeline before the user approves the review.
- Resolution is **automatic** (auto-write, flag low-confidence). Do NOT ask the
  user to confirm individual entity matches — that is logistics, not judgment.
- New facts stay in extraction-layer labels; curated nodes are only MATCH-linked,
  never relabeled or overwritten.
- Tip: dry-run the pipeline first (`kg.pipeline <json>` without `--commit`) to show
  the load plan if the user wants to see it before committing.
