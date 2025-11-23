"""
Robust Streamlit frontend for Post-Discharge POC.

Notes:
- Expects backend API at API_URL (default: http://localhost:8000).
- Uses safe request handling and shows helpful debug info for backend errors.
- Uses st.rerun() instead of the removed experimental API.
"""

import os
import uuid
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")
ST_TIMEOUT = int(os.getenv("STREAMLIT_REQUEST_TIMEOUT", "15"))

st.set_page_config(page_title="Post-Discharge Assistant - POC", layout="centered")

st.title("Post-Discharge Medical Assistant - POC")
st.caption("Demo only — not medical advice.")

# initialize session
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.history = []
    st.session_state.last_receptionist_resp = None

# show session id for debugging (optional)
with st.expander("Session info (click to view)"):
    st.write("Session id:", st.session_state.session_id)
    st.write("API URL:", API_URL)

# helper to call receptionist and show initial prompt (only once per session)
def ensure_receptionist_initialized():
    # if we already got an initial message, skip
    if st.session_state.history and any(role == "agent" for role, _ in st.session_state.history):
        return

    try:
        resp = requests.post(
            f"{API_URL}/receptionist/message",
            json={"session_id": st.session_state.session_id, "message": ""},
            timeout=ST_TIMEOUT,
        )
    except Exception as e:
        st.session_state.history.append(("agent", f"Receptionist init failed: {e}"))
        return

    # try parse JSON safely
    try:
        payload = resp.json()
    except Exception:
        st.session_state.history.append(("agent", f"Receptionist init returned non-JSON (status {resp.status_code})."))
        st.session_state.history.append(("agent", f"Raw: {resp.text[:1000]}"))
        return

    reply = payload.get("reply")
    if reply:
        st.session_state.history.append(("agent", reply))
        st.session_state.last_receptionist_resp = payload
    else:
        st.session_state.history.append(("agent", "Receptionist did not return an initial reply."))

# ensure initial receptionist greeting is present
ensure_receptionist_initialized()

# render the chat history
for role, text in st.session_state.history:
    if role == "system":
        st.info(text)
    elif role == "user":
        st.markdown(f"**You:** {text}")
    elif role == "agent":
        st.markdown(f"**Agent:** {text}")

# user input box
user_input = st.text_input("Enter message", key="input")

if st.button("Send"):
    if not user_input or not user_input.strip():
        st.warning("Type something before sending.")
        st.rerun()

    # append user message to history
    st.session_state.history.append(("user", user_input))

    # ---- Call receptionist endpoint ----
    try:
        resp_r = requests.post(
            f"{API_URL}/receptionist/message",
            json={"session_id": st.session_state.session_id, "message": user_input},
            timeout=ST_TIMEOUT
        )
    except Exception as e:
        st.session_state.history.append(("agent", f"Receptionist request failed: {e}"))
        st.rerun()

    # parse receptionist JSON safely
    try:
        r = resp_r.json()
    except Exception as e:
        st.session_state.history.append(("agent", f"Receptionist returned invalid JSON: {e}"))
        st.session_state.history.append(("agent", f"Raw response (truncated): {resp_r.text[:1000]}"))
        st.rerun()

    # show receptionist reply if any
    if r.get("reply"):
        st.session_state.history.append(("agent", r["reply"]))

    # If receptionist requests a handoff to clinical agent, call it
    if r.get("handoff"):
        try:
            resp_c = requests.post(
                f"{API_URL}/clinical/query",
                json={"session_id": st.session_state.session_id, "message": user_input},
                timeout=ST_TIMEOUT * 2
            )
        except Exception as e:
            st.session_state.history.append(("agent", f"Clinical Agent request failed: {e}"))
            st.rerun()

        # handle non-200 quickly
        if resp_c.status_code != 200:
            st.session_state.history.append(("agent", f"Clinical Agent backend error: {resp_c.status_code}"))
            # show text for debugging
            st.session_state.history.append(("agent", f"Debug (truncated): {resp_c.text[:1200]}"))
            st.rerun()

        # parse JSON safely
        try:
            c = resp_c.json()
        except Exception as e:
            st.session_state.history.append(("agent", f"Clinical Agent returned invalid JSON: {e}"))
            st.session_state.history.append(("agent", f"Raw (truncated): {resp_c.text[:1200]}"))
            st.rerun()

        # display clinical result
        if c.get("error"):
            st.session_state.history.append(("agent", f"Clinical Agent error: {c.get('error')}"))
        elif c.get("web"):
            st.session_state.history.append(("agent", "Clinical Agent: I searched the web (results below):"))
            # be careful with long web_results — stringify/truncate
            web_results = c.get("web_results", [])
            if not web_results:
                st.session_state.history.append(("agent", "Clinical Agent: No web results found."))
            else:
    # render each result as markdown with clickable link and short snippet
                for i, res in enumerate(web_results, start=1):
                    title = res.get("title") or f"Result {i}"
                    snippet = res.get("snippet") or ""
                    link = res.get("link") or ""
                    if link:
                        md = f"**{i}. [{title}]({link})**  \n{snippet}"
                    else:
                        md = f"**{i}. {title}**  \n{snippet}"
                    st.session_state.history.append(("agent", md))
        else:
            answer = c.get("answer")
            sources = c.get("sources")
            if answer:
                st.session_state.history.append(("agent", f"Clinical Agent: {answer}"))
            else:
                st.session_state.history.append(("agent", "Clinical Agent: No answer returned."))

            if sources:
                # show short citation list
                st.session_state.history.append(("agent", "Sources:"))
                for s in sources:
                    # s might be dict with 'ref' and 'excerpt'
                    st.session_state.history.append(("agent", str(s)))

    # finished handling this message — rerun to refresh UI
    st.rerun()

# small footer with troubleshooting tips
st.markdown("---")
