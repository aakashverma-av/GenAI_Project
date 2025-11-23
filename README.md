Post-Discharge AI Medical Assistant — POC

This repository contains all required code for the Post-Discharge AI Medical Assistant (POC).

Note:
The FAISS index files (index.faiss and index.pkl) and the knowledge source PDF (comprehensive-clinical-nephrology.pdf) are not uploaded to GitHub due to size constraints.
They are available in the email attachment.
Place them in the following paths before running the app:

data/faiss_index/index.faiss
data/faiss_index/index.pkl
data/comprehensive-clinical-nephrology.pdf


Empty placeholder files are included in the repository for convenience.

Executive Summary

This project implements a Proof-of-Concept Post-Discharge Medical Assistant using:

FastAPI backend

Streamlit frontend

Retrieval-Augmented Generation (RAG) with FAISS

Multi-agent architecture (Receptionist + Clinical Agent)

SQLite patient database

Tavily → Europe PMC web-search fallback

Azure GPT-4o for reasoning and clinical dialogue

The system is designed solely for demonstration and research and clearly displays “Not medical advice” in the UI.

Repository Structure
Key Files
File	Description
requirements.txt	Python dependencies (formatting may need adjustments)
streamlit_app.py	Streamlit frontend (UI, session state, API calls)
app/main.py	FastAPI backend with receptionist & clinical endpoints
app/agents.py	Receptionist agent + clinical agent logic and routing
app/db_tool.py	Patient DB initialization & lookup (SQLite)
app/rag.py	FAISS loading, embedding setup, RetrievalQA chain
app/index_builder.py	PDF text extraction, chunking, embedding, FAISS index building
app/web_search.py	Tiered web search (Tavily → Europe PMC)
app/logger_conf.py	Logging configuration (stored in app_logs/)
data/patients.json	Seed data (30 dummy patient discharge records)
data/patients.db	SQLite DB created from JSON
data/faiss_index/	FAISS index files (placeholders included)

Data Summary
1. Patient Dataset

30 synthetic patient discharge summaries

Includes: diagnosis, medications, diet, follow-up, warning signs, instructions

Loaded into SQLite at app startup

2. Knowledge Source for RAG

comprehensive-clinical-nephrology.pdf

Chunked & embedded into FAISS using index_builder.py

3. FAISS Vector Store

index.faiss and index.pkl

Stores prebuilt embeddings and metadata for fast retrieval

⚙️ Architecture & Data Flow

User interacts with Streamlit UI (streamlit_app.py)

UI sends queries to FastAPI backend

Backend routes messages to Receptionist Agent

Receptionist:

Asks for patient name

Looks up patient in SQLite

Determines if the query is clinical or general

For medical questions:

Receptionist hands off to Clinical Agent

Clinical Agent:

Runs RAG (FAISS → nephrology PDF)

If insufficient → triggers web search fallback (Tavily → Europe PMC)

All interactions + retrieval logs go to app_logs/

How to Run
1. Set up environment
python -m venv .venv
.\.venv\Scripts\activate    # Windows PowerShell
pip install -r requirements.txt

2. Create .env file (required)

Include:

AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_EMBED_DEPLOYMENT=
AZURE_OPENAI_CHAT_DEPLOYMENT=
OPENAI_API_VERSION=
BING_SEARCH_API_KEY=
FAISS_INDEX_PATH=data/faiss_index
NEPHRO_PDF_PATH=data/comprehensive-clinical-nephrology.pdf
SQLITE_DB_PATH=data/patients.db

3. (Optional) Rebuild FAISS index
python app/index_builder.py

4. Initialize patient DB (if needed)
python scripts/init_db_from_json.py

5. Start backend
uvicorn app.main:app --reload --port 8000

6. Start frontend
streamlit run streamlit_app.py --server.port=8501

Known/Expected Issues

requirements.txt may need formatting + version pinning

LangChain/OpenAI API signatures vary across versions

FAISS index must match the embedding model used

Environment variable names must be consistent across modules

Tavily API key is currently a placeholder → must be stored in .env

Requirement Mapping
1) Data Setup

✔ 30+ dummy discharge records
✔ Nephrology reference PDF
✔ SQLite DB with lookup
✔ FAISS index (embeddings + metadata)

2) Multi-Agent System

Receptionist → name lookup + routing

Clinical Agent → RAG + web search fallback

3) RAG Pipeline

PDF chunking

Embeddings + FAISS

Retrieval + answer generation with GPT-4o

Source citations returned

4) Web Search

Tavily API → general query retrieval

Europe PMC → clinical literature fallback

Used when RAG confidence is low or user asks for “latest research”

5) Logging

Structured logs for retrievals, errors, agent handoffs, and DB calls

6) Patient Data Retrieval

Robust name lookup

Handles missing/ambiguous patients

All DB access securely abstracted from agent logic
