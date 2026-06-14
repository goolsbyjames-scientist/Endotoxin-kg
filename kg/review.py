"""Render a verified extraction as a human-readable review (the judgment gate).

Run:  python -m kg.review data/extracted/PMC5302069.json

This is the ONE place a human is needed: checking that the structured extraction
faithfully represents the paper. It writes a Markdown review next to the JSON and
floats the adversarial verifier's flags to the top, so attention goes to the
claims most likely to be wrong (theoretical-not-experimental, figure-only data,
low confidence, conflict of interest).

Corrections are conversational: tell the agent what's wrong, it edits the gold
JSON, and re-runs this. Nothing is loaded until the review is approved.
"""

from __future__ import annotations

import json
import os
import sys

LOW_CONF = 0.75


def _flags(c: dict) -> list[str]:
    f = []
    if c.get("basis") in ("theoretical", "discussion"):
        f.append("THEORETICAL (not experimentally shown)")
    if c.get("verify"):
        f.append("verify")
    if c.get("data_in_figure_only"):
        f.append("figure-only data")
    if c.get("confidence", 1) < LOW_CONF:
        f.append(f"low-conf {c.get('confidence')}")
    return f


def render(ex: dict) -> str:
    doc = ex["document"]
    out: list[str] = []
    a = out.append

    a(f"# Review: {doc['title']}\n")
    a(f"Source: https://doi.org/{doc['doi']}  (PMID {doc['pmid']}, {doc['venue']} {doc['year']})\n")
    a(f"> Check each item against the paper. To fix something, just say so "
      f"(e.g. \"AC4 stance should be neutral\") and I'll edit the JSON and "
      f"regenerate this. Approve when it's right.\n")

    # --- priorities: what the verifier flagged ---
    flagged = [(c, _flags(c)) for c in ex["claims"]]
    flagged = [(c, f) for c, f in flagged if f]
    a("## ⚠ Review priorities (the verifier flagged these)\n")
    if not flagged:
        a("_Nothing flagged._\n")
    for c, f in flagged:
        a(f"- **{c['id']}** [{', '.join(f)}] — {c['text']}")
    coi = ex.get("conflict_of_interest")
    if coi:
        a(f"\n- **Conflict of interest:** declared *{coi.get('declared_by_authors','?')}*; "
          f"{coi.get('structural_coi','')}")
    a("")

    # --- methods ---
    a(f"## Methods ({len(ex['methods'])})\n")
    for m in ex["methods"]:
        a(f"- **{m['id']}** {m['name']}")
    a("")

    # --- preparations (the comparison spine) ---
    a(f"## Preparations ({len(ex['preparations'])})\n")
    for p in ex["preparations"]:
        a(f"- **{p['abbrev']}** — {p['name']}")
    a("")

    # --- claims, grouped, scannable ---
    for tier, head in (("atomic", "Atomic claims"), ("narrative", "Narrative claims")):
        rows = [c for c in ex["claims"] if c["tier"] == tier]
        a(f"## {head} ({len(rows)})\n")
        a("| ID | basis | stance | conf | claim |")
        a("|----|-------|--------|------|-------|")
        for c in rows:
            mark = " ⚠" if _flags(c) else ""
            text = c["text"].replace("|", "\\|")
            a(f"| {c['id']}{mark} | {c.get('basis','?')} | {c['stance']} | "
              f"{c.get('confidence','')} | {text} |")
        a("")
        # quotes underneath for spot-checking against the paper
        a("<details><summary>quotes & figures</summary>\n")
        for c in rows:
            q = c.get("quote", "")
            fig = c.get("evidence_figure", "")
            a(f"- **{c['id']}** ({fig}): \"{q}\"")
        a("\n</details>\n")

    a(f"## Tally\n")
    comp = ex.get("completeness", {})
    a(f"methods={comp.get('methods')} · preparations={comp.get('preparations')} · "
      f"atomic={comp.get('atomic')} · narrative={comp.get('narrative')}")
    return "\n".join(out)


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python -m kg.review <extraction.json>")
        raise SystemExit(2)
    path = sys.argv[1]
    with open(path, encoding="utf-8") as fh:
        ex = json.load(fh)

    md = render(ex)
    out_path = os.path.splitext(path)[0] + "_review.md"
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(md)

    n_flag = sum(1 for c in ex["claims"] if _flags(c))
    print(f"Wrote {out_path}")
    print(f"  {len(ex['claims'])} claims, {n_flag} flagged for your attention.")
    print("  Open it, check against the paper, and tell me any corrections.")


if __name__ == "__main__":
    main()
