from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any
import os
from dotenv import load_dotenv
load_dotenv()

from app.logger_conf import logger
from app.agents import receptionist_handle_message, clinical_handle_query
from app.db_tool import init_db

app = FastAPI(title="PostDischarge POC API")

# minimal in-memory session store (for POC)
SESSIONS = {}

class MessageIn(BaseModel):
    session_id: str
    message: str

@app.on_event("startup")
def startup_event():
    # initialize DB from data/patients.json if not present
    init_db(json_path=os.getenv("PATIENTS_JSON_PATH", "../data/patients.json"))
    logger.info("API started")

@app.post("/receptionist/message")
def receptionist_message(msg: MessageIn):
    sid = msg.session_id
    if sid not in SESSIONS:
        SESSIONS[sid] = {"stage": "ask_name"}
    session = SESSIONS[sid]
    res = receptionist_handle_message(session, msg.message)
    # save session back
    SESSIONS[sid] = session
    return res

@app.post("/clinical/query")
def clinical_query(msg: MessageIn):
    sid = msg.session_id
    session = SESSIONS.get(sid, {})
    res = clinical_handle_query(session, msg.message)
    return res
