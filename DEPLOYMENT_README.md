# 🦀 Endotoxin Testing RAG

A **Hybrid Retrieval-Augmented Generation (RAG)** system that searches a Neo4j knowledge graph to help find the right endotoxin testing products for pharmaceutical and biotech manufacturing.

## Architecture

- **Knowledge Graph:** Neo4j Aura (free tier) containing 29 products, 18 manufacturers, 16 regulatory documents, 10 regions
- **Embeddings:** Sentence Transformers (`all-MiniLM-L6-v2`) — vector search on product/method descriptions
- **Web Interface:** Streamlit for interactive product discovery
- **LLM (Optional):** Claude API for advanced synthesis (API key required)

## Features

✅ **Vector Search** — Find products using semantic similarity (not just keyword matching)  
✅ **Graph Traversal** — Get rich context (manufacturers, regulations, approvals)  
✅ **Product Recommendations** — Discover LAL, rFC, and rCR reagents by use case  
✅ **Regulatory Lookup** — See which compendial methods recognize each product  
✅ **Online & Shareable** — Deployed on Streamlit Cloud (free)  

## Data Included

| Category | Count |
|----------|-------|
| Products (LAL/rFC/rCR/Bacteriophage) | 29 |
| Manufacturers | 18 |
| Regulatory Methods (Compendial) | 16 |
| Regulatory Documents (FDA, EMA, USP, JP, etc.) | 16 |
| Patents | 11 |
| Regions | 10 |
| Market Segments | 6 |

## Quick Start (Local)

### Prerequisites
- Python 3.12+
- Git

### 1. Clone and Setup

```bash
git clone https://github.com/<your-username>/endotoxin-rag.git
cd endotoxin-rag

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Credentials

Create a `.env` file (git-ignored) with your Neo4j Aura credentials:

```env
# Neo4j Aura
NEO4J_URI=neo4j+s://YOUR_INSTANCE_ID.databases.neo4j.io
NEO4J_USERNAME=YOUR_USERNAME
NEO4J_PASSWORD=YOUR_PASSWORD
NEO4J_DATABASE=neo4j

# Claude API (optional, for LLM synthesis)
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Verify Connection

```bash
python -m kg.connection
```

Expected output:
```
Connected to Neo4j at <IP>:<PORT> (database 'YOUR_DB'). Server says: pong
```

### 4. Generate Embeddings (first time only)

```bash
python -m kg.embeddings
```

This embeds all product/method descriptions and creates vector indexes.

### 5. Run Streamlit App

```bash
streamlit run app.py
```

Visit http://localhost:8501

## Deployment to Streamlit Cloud (Free)

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial RAG deployment"
git remote add origin https://github.com/<your-username>/endotoxin-rag.git
git push -u origin main
```

### 2. Deploy via Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **New App**
3. Connect your GitHub repo
4. Select `main` branch and `app.py` as the entry point
5. Click **Deploy**

### 3. Add Secrets via Streamlit Cloud UI

Once deployed, go to App Settings → Secrets and paste:

```toml
neo4j_uri = "neo4j+s://YOUR_INSTANCE_ID.databases.neo4j.io"
neo4j_username = "YOUR_USERNAME"
neo4j_password = "YOUR_PASSWORD"
neo4j_database = "neo4j"
```

Your app will redeploy automatically and be live at `https://yourapp.streamlit.app`

## Architecture & Learning

### Hybrid RAG Flow

```
User Query
    ↓
[1] Embed Query (Sentence Transformers) → 384-dim vector
    ↓
[2] Vector Search Neo4j → top-K products by semantic similarity
    ↓
[3] Graph Traversal (Cypher) → rich context (mfg, regulations, regions)
    ↓
[4] Synthesis (Claude) → natural language response [OPTIONAL]
    ↓
Structured Results (JSON)
```

### Key Concepts

**Embeddings:** Convert text → dense vectors. Similar meaning → similar vectors.  
**Vector Indexes:** Fast (cosine) similarity search in Neo4j.  
**Graph Context:** Link products → manufacturers → regions → regulations.  
**LLM Synthesis:** Optional Claude call to create narrative answers.  

### Files

```
├── app.py                    # Streamlit web interface
├── kg/
│   ├── connection.py         # Neo4j driver setup
│   ├── explore.py            # Graph introspection
│   ├── query.py              # Domain example queries
│   ├── embeddings.py         # Generate & store embeddings
│   ├── rag.py                # Hybrid RAG search engine
│   └── load.py               # Cypher file runner
├── cypher/
│   ├── examples.cypher       # Neo4j Browser queries
│   └── ...
├── requirements.txt          # Python dependencies
├── .env                      # Secrets (git-ignored)
├── .streamlit/
│   ├── config.toml           # Streamlit theme/config
│   └── secrets.toml          # Streamlit secrets (git-ignored)
└── README.md                 # This file
```

## Customization

### Add More Products/Data

Edit Neo4j directly via [Neo4j Browser](https://console.neo4j.com) or run Cypher scripts:

```bash
python -m kg.load cypher/your_script.cypher
```

### Retrain Embeddings

After adding new products:

```bash
python -m kg.embeddings
```

### Use Different Embedding Model

Edit `kg/embeddings.py` and `kg/rag.py`:

```python
model = SentenceTransformer("all-mpnet-base-v2")  # Larger, slower, more accurate
```

## Troubleshooting

**Q: "ServiceUnavailable: Failed to DNS resolve" error**  
A: Check `.env` credentials. Make sure Neo4j Aura instance is running.

**Q: Slow searches?**  
A: Streamlit Cloud has cold starts. First query takes 30s (model loading). Subsequent queries are fast.

**Q: Want Claude synthesis back?**  
A: Get an API key from [anthropic.com](https://console.anthropic.com) and set `ANTHROPIC_API_KEY` in secrets.

## Learning Resources

- [Sentence Transformers Docs](https://www.sbert.net/)
- [Neo4j Vector Search](https://neo4j.com/docs/cypher-manual/current/indexes-search/semantic-indexes/vector-indexes/)
- [Streamlit Docs](https://docs.streamlit.io/)
- [Anthropic Claude API](https://docs.anthropic.com/)

## License

MIT (Learning project)

## Questions?

See `CLAUDE.md` for design notes and data modeling decisions.
