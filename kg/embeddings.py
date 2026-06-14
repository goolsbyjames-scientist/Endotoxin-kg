"""
Generate and store embeddings for endotoxin graph nodes.

Uses sentence-transformers to embed product/method/regulation descriptions,
then stores vectors in Neo4j for semantic search.
"""

import sys

from sentence_transformers import SentenceTransformer
from kg.connection import get_driver, get_database


def load_embedding_model():
    """Load the sentence transformer model (all-MiniLM-L6-v2)."""
    print("Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print(f"Model loaded. Embedding dimension: {model.get_sentence_embedding_dimension()}")
    return model


def embed_text(model, text: str) -> list[float]:
    """Embed a single text string."""
    if not text or not text.strip():
        return None
    return model.encode(text, convert_to_tensor=False).tolist()


def embed_products_and_methods():
    """Embed all Product and CompendialMethod nodes, store vectors in Neo4j."""
    driver = get_driver()
    db = get_database()
    model = load_embedding_model()

    with driver.session(database=db) as session:
        # Embed products
        print("\n--- Embedding Products ---")
        result = session.run(
            """
            MATCH (p:Product)
            WHERE p.description IS NOT NULL
            RETURN p.id, p.name, p.description
            LIMIT 100
            """
        )
        products = [record.data() for record in result]
        print(f"Found {len(products)} products to embed")

        for i, record in enumerate(products):
            prod_id = record["p.id"]
            name = record["p.name"]
            description = record["p.description"]

            # Embed description
            embedding = embed_text(model, description)
            if embedding:
                # Store embedding as vector in Neo4j
                session.run(
                    """
                    MATCH (p:Product {id: $id})
                    SET p.embedding = $embedding
                    """,
                    id=prod_id,
                    embedding=embedding,
                )
                if (i + 1) % 5 == 0:
                    print(f"  ✓ Embedded {i + 1}/{len(products)} products")

        # Embed compendial methods
        print("\n--- Embedding CompendialMethods ---")
        result = session.run(
            """
            MATCH (m:CompendialMethod)
            WHERE m.description IS NOT NULL
            RETURN m.id, m.name, m.description
            LIMIT 100
            """
        )
        methods = [record.data() for record in result]
        print(f"Found {len(methods)} methods to embed")

        for i, record in enumerate(methods):
            method_id = record["m.id"]
            name = record["m.name"]
            description = record["m.description"]

            embedding = embed_text(model, description)
            if embedding:
                session.run(
                    """
                    MATCH (m:CompendialMethod {id: $id})
                    SET m.embedding = $embedding
                    """,
                    id=method_id,
                    embedding=embedding,
                )
                if (i + 1) % 5 == 0:
                    print(f"  ✓ Embedded {i + 1}/{len(methods)} methods")

        print("\n✅ Embeddings stored in Neo4j")


def create_vector_indexes():
    """Create vector search indexes on Product and CompendialMethod."""
    driver = get_driver()
    db = get_database()

    with driver.session(database=db) as session:
        print("\n--- Creating Vector Indexes ---")

        # Check if Product index exists (try to create; ignore if exists)
        try:
            session.run(
                """
                CREATE VECTOR INDEX product_embeddings IF NOT EXISTS
                FOR (p:Product) ON (p.embedding)
                OPTIONS {indexConfig: {`vector.similarity_function`: 'cosine'}}
                """
            )
            print("✓ Vector index on Product.embedding created/verified (cosine)")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("✓ Product index already exists")
            else:
                print(f"⚠ Product index creation note: {e}")

        # Check if CompendialMethod index exists
        try:
            session.run(
                """
                CREATE VECTOR INDEX method_embeddings IF NOT EXISTS
                FOR (m:CompendialMethod) ON (m.embedding)
                OPTIONS {indexConfig: {`vector.similarity_function`: 'cosine'}}
                """
            )
            print("✓ Vector index on CompendialMethod.embedding created/verified (cosine)")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("✓ CompendialMethod index already exists")
            else:
                print(f"⚠ CompendialMethod index creation note: {e}")

        print("\n✅ Vector indexes configured")


def embed_extraction_nodes():
    """Embed extracted :Claim (text) and :Document (title) nodes for search.

    These are the nodes the ingestion pipeline adds. Embedding them lets the
    existing RAG layer (kg/rag.py) find claims and papers by meaning, not just
    the curated products it already searches.
    """
    driver = get_driver()
    db = get_database()
    model = load_embedding_model()

    with driver.session(database=db) as session:
        for label, prop in [("Claim", "text"), ("Document", "title")]:
            # elementId() lets us match a node back regardless of its key.
            result = session.run(
                f"""
                MATCH (n:{label})
                WHERE n.{prop} IS NOT NULL AND n.embedding IS NULL
                RETURN elementId(n) AS eid, n.{prop} AS text
                """
            )
            rows = [(r["eid"], r["text"]) for r in result]
            print(f"\n--- Embedding {len(rows)} :{label} nodes ---")
            for i, (eid, text) in enumerate(rows):
                emb = embed_text(model, text)
                if emb:
                    session.run(
                        "MATCH (n) WHERE elementId(n) = $eid SET n.embedding = $e",
                        eid=eid, e=emb,
                    )
                if (i + 1) % 10 == 0:
                    print(f"  ✓ {i + 1}/{len(rows)}")
    print("✅ Extraction-node embeddings stored")


def create_extraction_indexes():
    """Vector indexes for the extracted :Claim and :Document nodes."""
    driver = get_driver()
    db = get_database()
    with driver.session(database=db) as session:
        for name, label in [("claim_embeddings", "Claim"), ("document_embeddings", "Document")]:
            session.run(
                f"""
                CREATE VECTOR INDEX {name} IF NOT EXISTS
                FOR (n:{label}) ON (n.embedding)
                OPTIONS {{indexConfig: {{`vector.similarity_function`: 'cosine'}}}}
                """
            )
            print(f"✓ Vector index {name} on :{label}.embedding (cosine)")


def main():
    """Generate embeddings and create indexes.

    Default: the curated products/methods. `--extraction`: the new :Claim /
    :Document nodes added by the ingestion pipeline.
    """
    if "--extraction" in sys.argv:
        embed_extraction_nodes()
        create_extraction_indexes()
    else:
        embed_products_and_methods()
        create_vector_indexes()
    print("\n🎉 Embedding step complete!")


if __name__ == "__main__":
    main()
