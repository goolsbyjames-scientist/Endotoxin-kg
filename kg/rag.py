"""
Hybrid RAG engine for endotoxin graph.

Combines:
1. Vector search (semantic similarity on embeddings)
2. Graph traversal (Cypher queries for relationships)
3. Claude API (generation and reasoning)
"""

from sentence_transformers import SentenceTransformer
import anthropic
from kg.connection import get_driver, get_database


# Global model (lazy-loaded)
_model = None


def get_embedding_model():
    """Get or load the embedding model."""
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def vector_search_products(query: str, top_k: int = 5) -> list[dict]:
    """
    Search for products using vector similarity.
    
    Args:
        query: User question/request
        top_k: Number of results to return
        
    Returns:
        List of matching product nodes with similarity scores
    """
    driver = get_driver()
    db = get_database()
    model = get_embedding_model()
    
    # Embed the query
    query_embedding = model.encode(query, convert_to_tensor=False).tolist()
    
    with driver.session(database=db) as session:
        # Vector search on product embeddings
        result = session.run(
            """
            CALL db.index.vector.queryNodes('product_embeddings', $top_k, $embedding)
            YIELD node, score
            RETURN {
                id: node.id,
                name: node.name,
                chemistry: node.chemistry,
                description: node.description,
                family: node.family,
                status: node.status,
                score: score
            } AS product
            ORDER BY score DESC
            """,
            top_k=top_k,
            embedding=query_embedding,
        )
        
        products = [record["product"] for record in result]
        return products


def get_product_context(product_ids: list[str]) -> dict:
    """
    Fetch rich graph context for products.
    
    Includes: manufacturers, regions, regulatory methods, patents, segments.
    """
    driver = get_driver()
    db = get_database()
    
    with driver.session(database=db) as session:
        # Get manufacturers
        manufacturers_result = session.run(
            """
            MATCH (p:Product {id: $id})<-[:MANUFACTURES]-(c:Company)
            RETURN c.id, c.name, c.type
            """,
            id=product_ids[0] if product_ids else None,
        )
        manufacturers = [
            {"id": r[0], "name": r[1], "type": r[2]}
            for r in manufacturers_result
        ]
        
        # Get regulatory methods that recognize this product
        methods_result = session.run(
            """
            MATCH (p:Product {id: $id})<-[:RECOGNIZES]-(m:CompendialMethod)
            RETURN m.id, m.name, m.pharmacopoeia, m.recognizes_LAL, m.recognizes_rFC, m.recognizes_rCR
            """,
            id=product_ids[0] if product_ids else None,
        )
        methods = [
            {
                "id": r[0],
                "name": r[1],
                "pharmacopoeia": r[2],
                "recognizes_LAL": r[3],
                "recognizes_rFC": r[4],
                "recognizes_rCR": r[5],
            }
            for r in methods_result
        ]
        
        # Get regulatory documents relevant to this chemistry
        docs_result = session.run(
            """
            MATCH (p:Product {id: $id})
            MATCH (m:CompendialMethod)<-[:REFERENCES]-(d:RegulatoryDocument)
            WHERE (p:LAL AND m.recognizes_LAL) OR (p:rFC AND m.recognizes_rFC) OR (p:rCR AND m.recognizes_rCR)
            RETURN DISTINCT d.id, d.name, d.description, d.issuing_body
            """,
            id=product_ids[0] if product_ids else None,
        )
        docs = [
            {"id": r[0], "name": r[1], "description": r[2], "issuing_body": r[3]}
            for r in docs_result
        ]
        
        # Get regions where relevant
        regions_result = session.run(
            """
            MATCH (p:Product {id: $id})<-[:RECOGNIZES]-(m:CompendialMethod)-[:IN_FORCE_IN]->(reg:Region)
            RETURN DISTINCT reg.id, reg.name, reg.scope
            """,
            id=product_ids[0] if product_ids else None,
        )
        regions = [{"id": r[0], "name": r[1], "scope": r[2]} for r in regions_result]
        
        return {
            "manufacturers": manufacturers,
            "methods": methods,
            "regulatory_docs": docs,
            "regions": regions,
        }


def rag_search(query: str, region: str = None, regulatory_body: str = None) -> dict:
    """
    Hybrid RAG search (vector + graph).
    
    Returns structured search results + context instead of Claude generation.
    
    Args:
        query: User's natural language question
        region: Optional region filter (e.g., 'EU', 'US')
        regulatory_body: Optional regulator filter (e.g., 'FDA', 'EMA')
        
    Returns:
        Dictionary with products, manufacturers, methods, and regulatory context
    """
    # Step 1: Vector search for relevant products
    print(f"🔍 Searching for products related to: {query}")
    products = vector_search_products(query, top_k=5)
    
    if not products:
        return {
            "status": "no_results",
            "message": "No products found matching your query."
        }
    
    # Step 2: Fetch rich graph context
    product_ids = [p["id"] for p in products]
    context = get_product_context(product_ids)
    
    # Step 3: Return structured result
    result = {
        "status": "success",
        "query": query,
        "products": products,
        "manufacturers": context["manufacturers"],
        "regulatory_methods": context["methods"],
        "regulatory_documents": context["regulatory_docs"],
        "regions": context["regions"],
        "summary": f"Found {len(products)} products matching your query. " + 
                   f"{len(context['manufacturers'])} manufacturer(s) available. " +
                   f"Regulatory approval in {len(context['regions'])} region(s)."
    }
    
    return result


if __name__ == "__main__":
    # Test example
    import json
    result = rag_search(
        "What endotoxin testing products are available for pharmaceutical manufacturing?"
    )
    print("\n" + "=" * 60)
    print("RAG RESPONSE:")
    print("=" * 60)
    print(json.dumps(result, indent=2, default=str))

