"""Build and verify a Neo4j driver from environment settings.

This is the single place that knows how to connect. Everything else imports
`get_driver()` and `get_database()` so credentials live in exactly one spot
(your .env file), never in code.

The official `neo4j` driver gives you a `Driver` object that manages a pool of
connections. You create ONE per application and reuse it; you open short-lived
*sessions* per unit of work.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase

# Load .env from the project root (the parent of this file's "kg" package),
# so the scripts work no matter which directory you run them from.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

# Windows terminals default to the legacy cp1252 code page, which crashes when
# we print scientific text from the graph (Greek letters, arrows, °, ≥, …).
# Force UTF-8 so our scripts can print real-world data safely. Every runnable
# module imports from this one, so doing it here covers all of them.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass  # already UTF-8, or a stream that doesn't support reconfigure


class MissingConfig(RuntimeError):
    """Raised when required connection settings are absent or still placeholders."""


def _require(name: str) -> str:
    """Get config from Streamlit secrets (cloud) or environment variables (local)."""
    # Try Streamlit secrets first (running in Streamlit Cloud)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and len(st.secrets) > 0:
            # Streamlit secrets dict uses lowercase keys from TOML file
            secret_key_lower = name.lower()
            if secret_key_lower in st.secrets:
                value = st.secrets[secret_key_lower]
                if value and "CHANGE_ME" not in str(value):
                    return str(value).strip()
    except Exception:
        pass  # Not in Streamlit, secrets not loaded, or any other error
    
    # Fall back to environment variables (local development)
    value = os.getenv(name, "").strip()
    if not value or "CHANGE_ME" in value:
        raise MissingConfig(
            f"Configuration {name!r} is not set.\n"
            f"Local: Copy .env.example to .env and fill in your Neo4j Aura credentials.\n"
            f"Cloud: Add secrets via Streamlit Cloud UI (Settings → Secrets).\n"
            f"(See README.md or DEPLOYMENT_README.md for details.)"
        )
    return value


def get_database() -> str:
    """Return the target database name (defaults to 'neo4j', as Aura uses)."""
    return os.getenv("NEO4J_DATABASE", "neo4j").strip() or "neo4j"


def get_driver() -> Driver:
    """Construct a Neo4j Driver from .env. Caller is responsible for closing it.

    Prefer the context-manager form so the connection pool is always released:

        with get_driver() as driver:
            ...
    """
    uri = _require("NEO4J_URI")
    user = _require("NEO4J_USERNAME")
    password = _require("NEO4J_PASSWORD")
    return GraphDatabase.driver(uri, auth=(user, password))


def verify() -> None:
    """Open a driver, confirm connectivity, and print a friendly summary.

    Run directly:  python -m kg.connection
    """
    with get_driver() as driver:
        # Raises immediately with a clear error if the URI/credentials are wrong.
        driver.verify_connectivity()
        db = get_database()
        # A trivial round-trip query to prove the database answers.
        records, summary, _ = driver.execute_query(
            "RETURN 'pong' AS reply", database_=db
        )
        reply = records[0]["reply"]
        server = summary.server.address
        print(f"Connected to Neo4j at {server} (database '{db}'). Server says: {reply}")


if __name__ == "__main__":
    verify()
