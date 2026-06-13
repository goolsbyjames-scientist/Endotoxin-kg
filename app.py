"""
Streamlit web interface for Endotoxin Testing RAG.

Users can search for endotoxin testing products based on their
manufacturing needs, region, and regulatory requirements.
"""

import streamlit as st
import json
from kg.rag import rag_search


st.set_page_config(
    page_title="Endotoxin Testing Finder",
    page_icon="🦀",
    layout="wide",
)

st.title("🦀 Endotoxin Testing Product Finder")
st.markdown("""
Find the right endotoxin testing products for your pharmaceutical or biotech manufacturing.
This tool searches a knowledge graph of LAL, rFC, and rCR reagents, manufacturers, and regulatory approvals.
""")

# Sidebar for filters
st.sidebar.header("Search Filters")
search_query = st.sidebar.text_area(
    "What are you looking for?",
    placeholder="e.g., 'LAL products for pharma manufacturing'",
    height=80
)

region_filter = st.sidebar.selectbox(
    "Region (optional)",
    ["All", "US", "EU", "China", "Japan"],
)

chemistry_filter = st.sidebar.multiselect(
    "Chemistry preference",
    ["LAL", "rFC", "rCR", "Bacteriophage"],
    default=[]
)

# Main search
if st.sidebar.button("🔍 Search", use_container_width=True):
    if not search_query.strip():
        st.error("Please enter a search query.")
    else:
        with st.spinner("Searching graph..."):
            result = rag_search(search_query, region=region_filter)
        
        if result.get("status") == "success":
            st.success(result["summary"])
            
            # Display products
            st.subheader("📦 Products Found")
            products = result.get("products", [])
            
            if products:
                for i, product in enumerate(products, 1):
                    with st.expander(f"**{i}. {product['name']}** ({product['chemistry']}, {product['status']})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Chemistry:** {product['chemistry']}")
                            st.markdown(f"**Family:** {product['family']}")
                            st.markdown(f"**ID:** `{product['id']}`")
                        with col2:
                            st.markdown(f"**Status:** {product['status']}")
                            st.markdown(f"**Relevance Score:** {product['score']:.1%}")
                        
                        st.markdown(f"**Description:**\n{product['description']}")
            else:
                st.info("No products matched your search.")
            
            # Display manufacturers
            st.subheader("🏭 Manufacturers")
            manufacturers = result.get("manufacturers", [])
            if manufacturers:
                for mfg in manufacturers:
                    st.markdown(f"- **{mfg['name']}** ({mfg['type']})")
            else:
                st.info("No manufacturer data available for these products.")
            
            # Display regulatory methods
            st.subheader("⚖️ Regulatory Methods")
            methods = result.get("regulatory_methods", [])
            if methods:
                for method in methods:
                    st.markdown(f"- **{method['name']}** ({method['pharmacopoeia']})")
            else:
                st.info("No regulatory method recognition data available.")
            
            # Display regulatory documents
            st.subheader("📋 Regulatory Documents")
            docs = result.get("regulatory_documents", [])
            if docs:
                for doc in docs:
                    st.markdown(f"- **{doc['name']}** ({doc['issuing_body']})")
            else:
                st.info("No relevant regulatory documents found.")
            
            # Raw JSON for developers
            with st.expander("📊 View raw data (JSON)"):
                st.json(result)
        
        else:
            st.error(result.get("message", "Search failed."))

# Example searches in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### Example Searches")
examples = [
    "LAL testing for pharma",
    "rFC alternative to LAL",
    "rapid endotoxin testing",
    "FDA approved methods",
]
for example in examples:
    if st.sidebar.button(f"Try: {example}", use_container_width=True):
        st.session_state.search_query = example

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
**About:**
This tool searches a Neo4j knowledge graph of endotoxin testing products,
companies, regulatory documents, and compendial methods.

**Data:** LAL, rFC, rCR reagents | 29 products | 18 manufacturers | 16 regulations
""")
