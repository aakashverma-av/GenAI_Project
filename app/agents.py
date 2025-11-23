from typing import Dict, Any
from app.db_tool import lookup_patient_by_name
from app.rag import get_rag_chain
from app.logger_conf import logger
# from app.web_search import ddg_search
from app.web_search import web_search_combined
import re

# Receptionist Agent
def receptionist_handle_message(session: Dict[str, Any], message: str) -> Dict[str, Any]:
    """
    session: dict to maintain minimal state (e.g., {'stage': 'ask_name', 'patient': None })
    """
    stage = session.get("stage", "ask_name")
    logger.info("Receptionist handling message at stage %s: %s", stage, message)

    if stage == "ask_name":
        # ask patient's name
        session["stage"] = "awaiting_name"
        return {"reply": "Hello! I'm your post-discharge care assistant. What's your name?", "session": session}

    if stage == "awaiting_name":
        name = message.strip()
        results = lookup_patient_by_name(name)
        if not results:
            session["stage"] = "ask_name"
            logger.info("Patient not found for name: %s", name)
            return {"reply": f"Sorry, I couldn't find a record for '{name}'. Could you please confirm the full name?", "session": session}
        if len(results) > 1:
            session["stage"] = "disambiguate"
            session["candidates"] = results
            names = [r['patient_name'] for r in results]
            return {"reply": f"I found multiple patients: {', '.join(names)}. Which one is you?", "session": session}
        # single match
        patient = results[0]
        session["stage"] = "idle"
        session["patient"] = patient
        # greet and ask follow up
        reply = (f"Hi {patient['patient_name']}! I found your discharge report from {patient['data'].get('discharge_date')}. "
                 f"Primary diagnosis: {patient['data'].get('primary_diagnosis')}. How are you feeling today? Are you following your medication schedule?")
        return {"reply": reply, "session": session}

    if stage == "disambiguate":
        # user picks one of the candidates by name or id
        # try to match
        candidates = session.get("candidates", [])
        name = message.strip().lower()
        for c in candidates:
            if c['patient_name'].lower() == name or str(c['id']) == name:
                session['patient'] = c
                session['stage'] = 'idle'
                return {"reply": f"Matched {c['patient_name']}. How can I help you today?", "session": session}
        return {"reply": "I couldn't match that. Please provide exact patient name from the list.", "session": session}

    # Default: if stage idle and message seems clinical -> route to clinical agent
    if stage == "idle":
        if is_clinical_question(message):
            logger.info("Routing to Clinical Agent for message: %s", message)
            return {"reply": "This sounds medical. Connecting you to the Clinical Agent...", "handoff": True, "session": session}
        else:
            # Non-clinical conversation: ask simple follow-up question
            return {"reply": "Thanks for the update. Anything else I can help you with?", "session": session}

def is_clinical_question(text: str) -> bool:
    """
    Improved heuristic to detect clinical/intention-to-search/questions about latest research.
    Returns True for symptom questions, medication/dose, and explicit "latest/research/study" queries.
    """
    if not text:
        return False
    textl = text.lower()

    # symptom/urgent keywords (existing)
    clinical_triggers = [
        "pain", "swelling", "shortness of breath", "dyspnea", "urine",
        "medication", "dose", "fever", "bleeding", "worsen", "dizziness",
        "edema", "leg swelling", "ankle swelling", "fluid retention"
    ]
    if any(k in textl for k in clinical_triggers):
        return True

    # research / latest information keywords (new)
    research_triggers = [
        "latest", "recent", "research", "study", "studies", "trial", "evidence",
        "meta-analysis", "systematic review", "what's new", "what is new",
        "guidelines", "safety", "side effects"
    ]
    if any(k in textl for k in research_triggers):
        return True

    # drug-specific triggers (domain-specific; helpful)
    drug_triggers = ["sglt2", "sglt2i", "sglt2 inhibitor", "dapagliflozin", "empagliflozin", "canagliflozin", "ertugliflozin"]
    if any(k in textl for k in drug_triggers):
        return True

    # question style heuristics
    if textl.strip().startswith(("should i", "what should i", "do i need", "is it ok", "is it safe")):
        return True

    return False

# Clinical Agent
# from app.web_search import ddg_search

def clinical_handle_query(session: Dict[str, Any], question: str) -> Dict[str, Any]:
    logger.info("Clinical agent handling question: %s", question)
    qa = get_rag_chain()
    try:
        # use .invoke if chain supports it
        result = qa.invoke({"query": question}) if hasattr(qa, "invoke") else qa({"query": question})
        answer_text = result.get("result") or result.get("answer") or ""
        src_docs = result.get("source_documents", [])
        citations = []
        for i, doc in enumerate(src_docs, start=1):
            excerpt = (doc.page_content[:300]).replace("\n", " ")
            citations.append({"ref": f"ref#{i}", "excerpt": excerpt})

        # If the user explicitly asked for 'latest' or 'research' OR RAG did not find anything,
        # perform a DuckDuckGo search as fallback.
        question_l = question.lower()
        wants_latest = any(k in question_l for k in ["latest", "recent", "research", "study", "studies", "trial", "evidence"])
        if wants_latest or not answer_text.strip() or "not found in reference" in answer_text.lower():
            web_results = web_search_combined(question)
            return {"answer": None, "sources": citations, "web": True, "web_results": web_results}

        return {"answer": answer_text, "sources": citations, "web": False}
    except Exception as e:
        logger.exception("Clinical agent error: %s", e)
        return {"answer": None, "error": str(e)}

def web_search_placeholder(query: str):
    """
    Placeholder for web search. Integrate Bing or SerpAPI here.
    """
    logger.info("Performing web search for query (placeholder): %s", query)
    # return placeholder structure
    return [{"title": "Web result title (placeholder)", "link": "https://example.com", "snippet": "Summary snippet..."}]
