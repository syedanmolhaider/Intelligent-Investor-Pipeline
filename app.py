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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Pure dark mode background */
    .stApp {
        background-color: #0b0f19 !important;
        color: #e6edf3 !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Clean Minimal Header */
    .omni-header {
        font-family: 'Inter', sans-serif;
        font-size: 2.8rem;
        font-weight: 700;
        text-align: center;
        background: -webkit-linear-gradient(45deg, #4da8da, #007cc7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: 2rem;
        margin-bottom: 0px;
        letter-spacing: -1px;
    }
    
    .omni-subheader {
        font-family: 'Inter', sans-serif;
        color: #6e7681;
        text-align: center;
        margin-bottom: 4rem;
        font-size: 1.1rem;
        font-weight: 400;
    }

    /* ---------------- SLEEK AI CHAT STYLING ---------------- */
    /* Remove all box borders and hard backgrounds for a fluid, continuous chat interface */
    [data-testid="stChatMessageContent"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        padding-top: 0.2rem !important;
    }
    
    /* Subtle separation between messages */
    [data-testid="stChatMessage"] {
        padding: 1.5rem 0 !important;
        border-bottom: 1px solid rgba(255,255,255, 0.05);
    }
    
    /* Beautiful Typography for the chat text */
    .stChatMessage .stMarkdown p {
        font-family: 'Inter', sans-serif !important;
        font-size: 1.25rem !important; /* Huge readability boost */
        line-height: 1.75 !important;
        color: #ECECEC !important;
        font-weight: 400 !important;
    }
    
    .stChatMessage .stMarkdown li {
        font-family: 'Inter', sans-serif !important;
        font-size: 1.2rem !important;
        line-height: 1.7 !important;
        color: #D4D4D4 !important;
        margin-bottom: 0.6rem;
    }
    
    .stChatMessage .stMarkdown strong {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    
    /* Chat Input Bar Styling */
    [data-testid="stChatInput"] {
        border-radius: 20px !important;
        border: 1px solid #30363d !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5) !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='omni-header'>OmniCortex AI</h1>", unsafe_allow_html=True)
st.markdown("<p class='omni-subheader'>Advanced Quantitative Analysis Engine</p>", unsafe_allow_html=True)

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
                
                # Fetch the intelligent response from Langgraph core
                response = brain.invoke(
                    {"messages": chat_history + [HumanMessage(content=prompt)]}
                )
                
                ai_reply = response["messages"][-1].content
                st.markdown(ai_reply)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                
            except Exception as e:
                error_trace = traceback.format_exc()
                logger.error("OmniCortex crashed with traceback:\n%s", error_trace)
                st.error(f"Execution Error: {str(e)}")
                st.markdown(f"**Detailed AI Logger:**\n```python\n{error_trace}\n```")

