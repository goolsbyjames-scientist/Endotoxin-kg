"""Agentic terminal chat over the knowledge graph (no Streamlit).

Run:  python -m kg.chat                 # interactive chat loop
      python -m kg.chat --once "..."    # single question (testable / scriptable)

This is a small *tool-using agent*. Each turn, Claude decides which tool fits the
question — and that choice is the whole lesson about graph + embeddings:

  * cypher_query   -> a READ-ONLY Cypher query, for STRUCTURAL questions:
                      counting, listing, filtering, relationships
                      ("how many rFC reagents?", "which companies make rCR?").
                      Exact and complete. This is what embeddings CANNOT do.
  * search_claims  -> semantic vector search over paper :Claim nodes, for FUZZY
                      questions ("what does the literature say about sensitivity?").
                      Approximate, meaning-based.

Embeddings find similar things; they do not count or enumerate. The graph does
that. Giving Claude both tools lets it use each for what it is good at.

Needs ANTHROPIC_API_KEY in .env. Type 'exit' to quit.
"""

from __future__ import annotations

import json
import os
import re
import sys

import anthropic

from kg.connection import get_driver, get_database
from kg.rag import vector_search_claims

MODEL = "claude-sonnet-4-6"

# Reject anything that could mutate the graph — the agent is read-only.
_WRITE = re.compile(r"\b(create|merge|delete|set|remove|drop|foreach)\b|load\s+csv", re.I)

TOOLS = [
    {
        "name": "cypher_query",
        "description": (
            "Run a READ-ONLY Cypher query against the BET knowledge graph and get rows back. "
            "Use for STRUCTURAL questions: counts, lists, filters, relationships "
            "(e.g. 'how many rFC products', 'which companies make rCR', 'patents owned by X'). "
            "Returns up to 50 rows as JSON. Only MATCH/RETURN/WHERE/WITH/ORDER/LIMIT etc. — no writes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "A read-only Cypher query."}},
            "required": ["query"],
        },
    },
    {
        "name": "search_claims",
        "description": (
            "Semantic vector search over extracted paper :Claim nodes. Use for FUZZY/CONCEPTUAL "
            "questions about the literature (e.g. 'what is known about rFC vs LAL sensitivity'). "
            "Returns the most similar claims with their source paper, stance and basis."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "top_k": {"type": "integer", "description": "default 6"},
            },
            "required": ["text"],
        },
    },
]


def _schema_text(driver, db) -> str:
    rels, _, _ = driver.execute_query(
        """MATCH (a)-[r]->(b)
           RETURN labels(a)[0] AS s, type(r) AS rel, labels(b)[0] AS t, count(*) AS c
           ORDER BY c DESC LIMIT 40""",
        database_=db,
    )
    return "\n".join(f"(:{r['s']})-[:{r['rel']}]->(:{r['t']})" for r in rels)


def _system(schema: str) -> str:
    return (
        "You answer questions about a Neo4j knowledge graph on Bacterial Endotoxins Testing (BET) "
        "by calling tools. Pick the right tool:\n"
        "- STRUCTURAL (how many / which / list / who makes / relationships) -> cypher_query.\n"
        "- FUZZY/CONCEPTUAL (what is known about / why / compare findings) -> search_claims.\n\n"
        "Graph conventions:\n"
        "- Products are multi-label: every product is :Product:Reagent PLUS a chemistry label "
        ":LAL / :rFC / :rCR / :Bacteriophage. Filter chemistry by LABEL (WHERE p:rFC), never a property.\n"
        "- Business key is `id`; `name` is the human label. Patents use `number`.\n"
        "- Extracted paper claims are :Claim with `basis` (experimental/computational/theoretical/"
        "discussion) and `stance`; papers are :Document.\n\n"
        f"Live schema (source -> rel -> target):\n{schema}\n\n"
        "Cite sources (product/company ids, or paper ids like PMC5302069). Respect claim stance/basis: "
        "a 'theoretical'/'discussion' claim is an argument, not a demonstrated result. If a query "
        "returns nothing, say so plainly."
    )


def main() -> None:
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Set ANTHROPIC_API_KEY in your .env to enable chat.")
        raise SystemExit(1)

    client = anthropic.Anthropic()
    driver = get_driver()
    db = get_database()
    system = _system(_schema_text(driver, db))

    def run_tool(name: str, inp: dict) -> str:
        if name == "cypher_query":
            q = inp.get("query", "")
            if _WRITE.search(q):
                return "REJECTED: this agent is read-only (no create/merge/delete/set/remove)."
            try:
                recs, _, _ = driver.execute_query(q, database_=db)
                rows = [r.data() for r in recs][:50]
                return json.dumps(rows, default=str) if rows else "(no rows)"
            except Exception as e:  # surface query errors back to the model to retry
                return f"ERROR: {e}"
        if name == "search_claims":
            hits = vector_search_claims(inp["text"], inp.get("top_k", 6))
            return json.dumps(hits, default=str)
        return f"unknown tool {name}"

    def answer(history: list[dict], question: str) -> str:
        history.append({"role": "user", "content": question})
        while True:
            resp = client.messages.create(
                model=MODEL, max_tokens=900, system=system, tools=TOOLS, messages=history
            )
            history.append({"role": "assistant", "content": resp.content})
            if resp.stop_reason != "tool_use":
                return "".join(b.text for b in resp.content if b.type == "text")
            results = []
            for b in resp.content:
                if b.type == "tool_use":
                    print(f"   ...{b.name}({json.dumps(b.input)[:80]})")
                    results.append({
                        "type": "tool_result", "tool_use_id": b.id,
                        "content": run_tool(b.name, b.input),
                    })
            history.append({"role": "user", "content": results})

    history: list[dict] = []
    if "--once" in sys.argv:
        i = sys.argv.index("--once")
        print(answer(history, " ".join(sys.argv[i + 1:]).strip()))
        return

    print("Knowledge-graph chat (graph + literature). Type 'exit' to quit.")
    print("(first question loads the embedding model — ~15s)\n")
    while True:
        try:
            q = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not q:
            continue
        if q.lower() in ("exit", "quit"):
            break
        print(f"\ngraph> {answer(history, q)}\n")


if __name__ == "__main__":
    main()
