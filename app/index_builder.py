"""
Chunk the nephrology PDF, create embeddings with Azure OpenAI and build a FAISS index.
"""
import os
from pathlib import Path
from typing import List
import pdfplumber
from tqdm import tqdm
import nltk
nltk.download('punkt')
from nltk.tokenize import sent_tokenize

# try this replacement in your code
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

from dotenv import load_dotenv
load_dotenv()

from app.logger_conf import logger

AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
EMBED_DEPLOY = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT")
INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")
PDF_PATH = os.getenv("NEPHRO_PDF_PATH", "./data/comprehensive-clinical-nephrology.pdf")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION", "2024-12-01-preview")

def extract_text_from_pdf(pdf_path: str) -> str:
    text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            ptext = page.extract_text()
            if ptext:
                text.append(ptext)
    return "\n\n".join(text)

def chunk_text(text: str) -> List[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", "!", "?"]
    )
    return splitter.split_text(text)

def build_faiss_index():
    os.makedirs(INDEX_PATH, exist_ok=True)
    logger.info("Extracting text from %s", PDF_PATH)
    text = extract_text_from_pdf(PDF_PATH)
    if not text:
        raise RuntimeError("No text extracted from nephrology PDF.")
    logger.info("Chunking text ...")
    chunks = chunk_text(text)
    logger.info("Chunks created: %d", len(chunks))

    # LangChain OpenAIEmbeddings (Azure): specify deployment name in client args
    embeddings = AzureOpenAIEmbeddings(
        deployment=EMBED_DEPLOY,
        chunk_size=1,
        openai_api_key=AZURE_API_KEY,
        azure_endpoint=AZURE_ENDPOINT,
        # openai_api_type="azure",
        openai_api_version=OPENAI_API_VERSION
    )

    logger.info("Embedding chunks and building FAISS index...")
    vectorstore = FAISS.from_texts(chunks, embeddings)
    vectorstore.save_local(INDEX_PATH)
    logger.info("FAISS index saved to %s", INDEX_PATH)

if __name__ == "__main__":
    build_faiss_index()
