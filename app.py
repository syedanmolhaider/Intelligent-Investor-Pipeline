import streamlit as st
import os
import json
import io
from contextlib import redirect_stdout
from google.cloud import bigquery
import pandas as pd
import logging
import traceback

# Setup detailed logging for the user's AI assistant
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CrewAIAssistant")

# ----------------- AUTHENTICATION HANDLING -----------------
# For Streamlit Community Cloud Deployment
if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or not os.path.exists(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "bq-key.json")):
    if "gcp_service_account" in st.secrets:
        # Reconstruct the bq-key.json file from Streamlit secrets
        with open("bq-key.json", "w") as f:
            f.write(json.dumps(dict(st.secrets["gcp_service_account"])))
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bq-key.json"
    elif os.path.exists("bq-key.json"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bq-key.json"
    else:
        st.error("BigQuery Key missing! Please authenticate.")

# Set GROQ Key for Streamlit Cloud
if not os.environ.get("GROQ_API_KEY") and "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

# ----------------- UI / DESIGN SETUP -----------------
st.set_page_config(page_title="Intelligent Investor AI", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    .main-header {
        font-family: 'Inter', sans-serif;
        background: -webkit-linear-gradient(45deg, #FFD700, #FFA500);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0;
        padding-top: 2rem;
    }
    .sub-header {
        font-family: 'Inter', sans-serif;
        color: #8b949e;
        text-align: center;
        margin-bottom: 3rem;
        font-size: 1.2rem;
    }
    .cio-verdict {
        font-size: 1.5rem;
        font-weight: bold;
        padding: 20px;
        border-radius: 10px;
        background: rgba(46, 160, 67, 0.1);
        border: 1px solid #2ea043;
        color: #3fb950;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 2rem;
    }
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>The Intelligent Investor AI</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Benjamin Graham Value Investing Engine for the Pakistan Market (Langchain + Groq LLM)</p>", unsafe_allow_html=True)

# ----------------- CHAT UI / MEMORY SETUP -----------------
# Initialize chat history memory
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome to **OmniCortex**, your elite quantitative AI for the Pakistan Market.\n\nAsk me anything! For example:\n- *What are the current metrics for MEBL.KA?*\n- *Any latest news on the State Bank of Pakistan?*\n- *What is the margin of safety for Mutual Fund X?*"}
    ]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ----------------- CONVERSATIONAL AI BRAIN -----------------
# Lazy load the brain
@st.cache_resource
def load_brain():
    from core_brain import get_omnicortex_brain
    return get_omnicortex_brain()

# React to user input
if prompt := st.chat_input("Talk with OmniCortex... (e.g. Analyze HUBC.KA)"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner("OmniCortex is thinking (and checking exact SQL/News data)..."):
            try:
                brain = load_brain()
                
                # We need to pass the conversation history properly
                from langchain_core.messages import HumanMessage, AIMessage
                chat_history = []
                for msg in st.session_state.messages[:-1]: # Don't include the immediate prompt, it's passed as 'input'
                    if msg["role"] == "user":
                        chat_history.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        chat_history.append(AIMessage(content=msg["content"]))
                
                # Fetch the intelligent response from Langchain core
                response = brain.invoke(
                    {"input": prompt, "chat_history": chat_history}
                )
                
                ai_reply = response["output"]
                st.markdown(ai_reply)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                
            except Exception as e:
                error_trace = traceback.format_exc()
                logger.error("OmniCortex crashed with traceback:\n%s", error_trace)
                st.error(f"Execution Error: {str(e)}")
                st.markdown(f"**Detailed AI Logger:**\n```python\n{error_trace}\n```")

