import os
import logging
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

from app.logger_conf import logger

# langchain imports 
import os
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import FAISS
# from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import AzureChatOpenAI
from langchain_classic.chains import RetrievalQA
from langchain_classic.prompts import PromptTemplate
from dotenv import load_dotenv
load_dotenv()
# try to import sentence-transformers for local fallback
try:
    from sentence_transformers import SentenceTransformer
    from langchain.embeddings import HuggingFaceEmbeddings
    _hf_available = True
except Exception:
    _hf_available = False

# env vars
INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")
AZURE_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")  
CHAT_DEPLOY = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
EMBED_DEPLOY = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION", "2024-06-01")

_cached_vectorstore = None
_cached_qa = None

def _try_make_azure_embeddings():
    """
    Try multiple constructor signatures for OpenAIEmbeddings to handle different langchain/openai versions.
    Returns an embeddings object on success, or raises the last exception on failure.
    """
    errs = []
    # Attempt 1: common signature used in many examples
    try:
        emb = AzureOpenAIEmbeddings(
            deployment=EMBED_DEPLOY,
            openai_api_key=AZURE_KEY,
            azure_endpoint=AZURE_ENDPOINT,
            openai_api_version=OPENAI_API_VERSION
        )
        logger.info("OpenAIEmbeddings constructed with (deployment, azure_endpoint, openai_api_version).")
        return emb
    except Exception as e:
        errs.append(("deployment+azure_endpoint+api_version", e))

    # Attempt 2: alias names some versions expect
    try:
        emb = AzureOpenAIEmbeddings(
            deployment_name=EMBED_DEPLOY,
            openai_api_key=AZURE_KEY,
            azure_endpoint=AZURE_ENDPOINT,
            openai_api_version=OPENAI_API_VERSION
        )
        logger.info("OpenAIEmbeddings constructed with (deployment_name, azure_endpoint, openai_api_version).")
        return emb
    except Exception as e:
        errs.append(("deployment_name+azure_endpoint+api_version", e))

    # Attempt 3: older alias 'azure_deployment' or 'azure_deployment_name'
    try:
        emb = AzureOpenAIEmbeddings(
            azure_deployment=EMBED_DEPLOY,
            openai_api_key=AZURE_KEY,
            azure_endpoint=AZURE_ENDPOINT,
            openai_api_version=OPENAI_API_VERSION
        )
        logger.info("OpenAIEmbeddings constructed with (azure_deployment, azure_endpoint, openai_api_version).")
        return emb
    except Exception as e:
        errs.append(("azure_deployment+azure_endpoint+api_version", e))

    # Attempt 4: some versions expect 'deployment' but 'azure_endpoint' named `openai_api_base` (less likely)
    try:
        emb = AzureOpenAIEmbeddings(
            deployment=EMBED_DEPLOY,
            openai_api_key=AZURE_KEY,
            openai_api_base=AZURE_ENDPOINT,
            openai_api_version=OPENAI_API_VERSION
        )
        logger.info("OpenAIEmbeddings constructed with (deployment, openai_api_base, openai_api_version).")
        return emb
    except Exception as e:
        errs.append(("deployment+openai_api_base+api_version", e))

    # Attempt 5: try 'model' param (some versions prefer model instead of deployment)
    try:
        emb = AzureOpenAIEmbeddings(
            model=EMBED_DEPLOY,
            openai_api_key=AZURE_KEY,
            azure_endpoint=AZURE_ENDPOINT,
            openai_api_version=OPENAI_API_VERSION
        )
        logger.info("OpenAIEmbeddings constructed with (model, azure_endpoint, openai_api_version).")
        return emb
    except Exception as e:
        errs.append(("model+azure_endpoint+api_version", e))

    # If none worked, raise a combined error (but keep the list for debugging)
    logger.error("All attempts to construct Azure OpenAI embeddings failed. Attempts and errors:")
    for name, ex in errs:
        logger.error("Attempt %s error: %s", name, repr(ex))
    raise RuntimeError("Failed to construct OpenAIEmbeddings for Azure. See logs for details.")

def _make_fallback_local_embeddings():
    """
    Create a local embedding object using sentence-transformers if available.
    This allows you to test the pipeline without Azure keys.
    """
    if not _hf_available:
        raise RuntimeError("No Azure embeddings available and sentence-transformers not installed. Install sentence-transformers to use local fallback.")
    # pick a small local model (adjust if you have others)
    model_name = "all-MiniLM-L6-v2"
    logger.info("Using local SentenceTransformer model for embeddings: %s", model_name)
    hf = SentenceTransformer(model_name)
    return HuggingFaceEmbeddings(model_name=model_name)

def load_vectorstore():
    """
    Load FAISS index using whichever embeddings we can construct.
    If embeddings construction fails for Azure, attempt local HF fallback (so testing can continue).
    """
    global _cached_vectorstore
    if _cached_vectorstore is not None:
        return _cached_vectorstore

    # First try Azure embeddings
    try:
        embeddings = _try_make_azure_embeddings()
    except Exception as e:
        logger.warning("Azure embeddings construction failed: %s", e)
        # Try local fallback
        try:
            embeddings = _make_fallback_local_embeddings()
            logger.info("Local HF embeddings created as fallback.")
        except Exception as e2:
            logger.exception("Local fallback also failed: %s", e2)
            raise RuntimeError("Failed to obtain any embeddings backend.") from e2

    # Now load FAISS index using the embeddings object
    try:
        vs = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        logger.info("Loaded FAISS index from %s", INDEX_PATH)
    except Exception as e:
        logger.exception("Failed to load FAISS index: %s", e)
        raise
    _cached_vectorstore = vs
    return vs

def get_rag_chain():
    """
    Build and cache a RetrievalQA chain using AzureChatOpenAI.
    Ensure openai_api_version is passed.
    """
    global _cached_qa
    if _cached_qa is not None:
        return _cached_qa

    # create chat model (explicit azure params)
    chat = AzureChatOpenAI(
        deployment_name=CHAT_DEPLOY,
        openai_api_key=AZURE_KEY,
        azure_endpoint=AZURE_ENDPOINT,
        openai_api_version=OPENAI_API_VERSION,
        temperature=0.2,
        max_tokens=800
    )

    vs = load_vectorstore()
    retriever = vs.as_retriever(search_type="similarity", search_kwargs={"k": 4})

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=(
            "You are a clinical assistant using nephrology reference materials.\n"
            "Use the context to answer the question. Include short citations like [ref#<i>] referencing the context sections.\n"
            "If the answer is not present in the context, say 'not found in reference' and optionally suggest to search web.\n\n"
            "CONTEXT:\n{context}\n\nQUESTION:\n{question}\n\nAnswer:"
        )
    )

    qa = RetrievalQA.from_chain_type(
        llm=chat,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )

    _cached_qa = qa
    logger.info("RAG chain initialized and cached.")
    return qa
