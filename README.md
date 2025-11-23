# Post-Discharge AI Medical Assistant — POC

This repository contains all required code for the **Post-Discharge AI Medical Assistant (POC)**.

> **Note:**  
> The FAISS index files (`index.faiss`, `index.pkl`) and the knowledge source PDF (`comprehensive-clinical-nephrology.pdf`) are **not uploaded** due to size limits.  
> They are available in the **email attachment**.  
> Place them here before running the app:
>
> ```
> data/faiss_index/index.faiss
> data/faiss_index/index.pkl
> data/comprehensive-clinical-nephrology.pdf
> ```
>
> Empty placeholder files are included in the repository.
> ### Download Full FAISS Index Bundle
- [faiss_index_bundle](<https://drive.google.com/drive/folders/16ToP89xcbpdFOHY03RCGU3mMm0Rvqvrc?usp=sharing>

---

## Executive Summary

This POC implements a lightweight **Post-Discharge Medical Assistant** using:

- **FastAPI** backend  
- **Streamlit** frontend  
- **Retrieval-Augmented Generation (RAG)** with FAISS  
- **Multi-agent architecture** (Receptionist + Clinical Agent)  
- **SQLite** patient database  
- **Tavily → Europe PMC** web-search fallback  
- **Azure GPT-4o** for clinical reasoning  

The system is for **demonstration and research only** and clearly displays **“Not medical advice”** in the UI.

---

## Repository Structure

### Key Files

| File | Description |
|------|-------------|
| `requirements.txt` | Python dependencies (may require formatting adjustments) |
| `streamlit_app.py` | Streamlit UI (session state, routing, API calls) |
| `app/main.py` | FastAPI backend (receptionist + clinical endpoints) |
| `app/agents.py` | Receptionist agent + clinical agent; routing logic |
| `app/db_tool.py` | SQLite DB initialization + patient lookup |
| `app/rag.py` | FAISS loading, embeddings, RetrievalQA chain |
| `app/index_builder.py` | PDF extraction, chunking, embeddings, FAISS builder |
| `app/web_search.py` | Tiered web search (Tavily → Europe PMC) |
| `app/logger_conf.py` | Logging configuration (`app_logs/`) |
| `data/patients.json` | Seed dataset (30 dummy patient records) |
| `data/patients.db` | SQLite DB created from JSON |
| `data/faiss_index/` | Placeholder for FAISS files |

---

## Data Summary

### Patient Dataset
- 30 synthetic patient discharge summaries  
- Includes diagnosis, medications, follow-up, warning signs, diet, and instructions  
- Loaded into SQLite at startup

### Knowledge Source for RAG
- `comprehensive-clinical-nephrology.pdf`  
- Chunked & embedded via `index_builder.py`

### FAISS Vector Store
- `index.faiss` + `index.pkl`  
- Prebuilt embeddings + metadata for fast retrieval

---

## Architecture & Data Flow

1. User interacts with **Streamlit UI** (`streamlit_app.py`)
2. UI sends message to **FastAPI backend**
3. Backend routes message to **Receptionist Agent**
4. Receptionist:  
   - asks for patient name  
   - looks up patient in SQLite  
   - determines if query is clinical or general
5. If medical → **handoff to Clinical Agent**
6. Clinical Agent:  
   - runs **RAG** (FAISS → nephrology PDF)  
   - if insufficient → triggers **web search fallback**
7. All steps logged in `app_logs/`

---

## How to Run

### 1. Create virtual environment
```bash
python -m venv .venv
.\.venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 2. Create `.env` file
```
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_EMBED_DEPLOYMENT=
AZURE_OPENAI_CHAT_DEPLOYMENT=
OPENAI_API_VERSION=
BING_SEARCH_API_KEY=
FAISS_INDEX_PATH=data/faiss_index
NEPHRO_PDF_PATH=data/comprehensive-clinical-nephrology.pdf
SQLITE_DB_PATH=data/patients.db
```

### 3. (Optional) Rebuild FAISS index
```bash
python app/index_builder.py
```

### 4. Initialize patient DB
```bash
python scripts/init_db_from_json.py
```

### 5. Start FastAPI backend
```bash
uvicorn app.main:app --reload --port 8000
```

### 6. Start Streamlit frontend
```bash
streamlit run streamlit_app.py --server.port=8501
```

---

- Handles ambiguous/missing inputs  
- DB abstraction prevents LLM from direct DB access
