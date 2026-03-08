import streamlit as st
import os
import json
import traceback
import logging

# Setup logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("OmniCortex")

# ----------------- AUTHENTICATION HANDLING -----------------
# For Streamlit Community Cloud Deployment
if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or not os.path.exists(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "bq-key.json")):
    if "gcp_service_account" in st.secrets:
        with open("bq-key.json", "w") as f:
            f.write(json.dumps(dict(st.secrets["gcp_service_account"])))
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bq-key.json"
    elif os.path.exists("bq-key.json"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bq-key.json"
    else:
        st.error("BigQuery Key missing! Please authenticate.")

# Set Google API Key for Streamlit Cloud
if not os.environ.get("GOOGLE_API_KEY") and "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]

# ----------------- UI / DESIGN SETUP -----------------
st.set_page_config(
    page_title="OmniCortex AI | Quant Committee",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');

    /* ============ CORE DARK THEME ============ */
    .stApp {
        background: linear-gradient(180deg, #080c14 0%, #0d1117 50%, #0b0f19 100%) !important;
        color: #e6edf3 !important;
        font-family: 'Inter', -apple-system, sans-serif !important;
    }

    /* ============ HEADER STYLING ============ */
    .omni-header {
        font-family: 'Inter', sans-serif;
        font-size: 3.2rem;
        font-weight: 700;
        text-align: center;
        background: linear-gradient(135deg, #58a6ff 0%, #1f6feb 40%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-top: 1.5rem;
        margin-bottom: 0px;
        letter-spacing: -1.5px;
    }

    .omni-subheader {
        font-family: 'JetBrains Mono', monospace;
        color: #6e7681;
        text-align: center;
        margin-bottom: 0.5rem;
        font-size: 0.85rem;
        font-weight: 400;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    .omni-tagline {
        font-family: 'Inter', sans-serif;
        color: #484f58;
        text-align: center;
        margin-bottom: 3rem;
        font-size: 0.75rem;
        font-style: italic;
    }

    /* ============ STATUS INDICATOR ============ */
    .status-bar {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin-bottom: 2rem;
        padding: 0.6rem 1.5rem;
        background: rgba(22, 27, 34, 0.6);
        border: 1px solid rgba(48, 54, 61, 0.5);
        border-radius: 12px;
        max-width: 600px;
        margin-left: auto;
        margin-right: auto;
    }

    .status-item {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        color: #8b949e;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }

    .status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        display: inline-block;
    }

    .status-dot.green { background: #3fb950; box-shadow: 0 0 6px #3fb950; }
    .status-dot.blue { background: #58a6ff; box-shadow: 0 0 6px #58a6ff; }
    .status-dot.purple { background: #8b5cf6; box-shadow: 0 0 6px #8b5cf6; }

    /* ============ CHAT STYLING ============ */
    [data-testid="stChatMessageContent"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        padding-top: 0.2rem !important;
    }

    [data-testid="stChatMessage"] {
        padding: 1.5rem 0 !important;
        border-bottom: 1px solid rgba(255,255,255, 0.04);
    }

    /* Chat Typography */
    .stChatMessage .stMarkdown p {
        font-family: 'Inter', sans-serif !important;
        font-size: 1.15rem !important;
        line-height: 1.8 !important;
        color: #e6edf3 !important;
        font-weight: 400 !important;
    }

    .stChatMessage .stMarkdown li {
        font-family: 'Inter', sans-serif !important;
        font-size: 1.1rem !important;
        line-height: 1.7 !important;
        color: #d4d4d4 !important;
        margin-bottom: 0.5rem;
    }

    .stChatMessage .stMarkdown strong {
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    .stChatMessage .stMarkdown h3 {
        font-family: 'Inter', sans-serif !important;
        color: #58a6ff !important;
        font-size: 1.3rem !important;
        border-bottom: 1px solid rgba(88, 166, 255, 0.15);
        padding-bottom: 0.5rem;
        margin-top: 1.5rem;
    }

    /* Persona section styling */
    .stChatMessage .stMarkdown h3 + p strong:first-child {
        color: #58a6ff !important;
    }

    /* Code blocks in chat (for error traces) */
    .stChatMessage .stMarkdown code {
        font-family: 'JetBrains Mono', monospace !important;
        background: rgba(22, 27, 34, 0.8) !important;
        color: #79c0ff !important;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.85rem;
    }

    /* Chat Input Bar */
    [data-testid="stChatInput"] {
        border-radius: 16px !important;
        border: 1px solid #30363d !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important;
        background: rgba(13, 17, 23, 0.8) !important;
    }

    [data-testid="stChatInput"] textarea {
        font-family: 'Inter', sans-serif !important;
        font-size: 1rem !important;
        color: #e6edf3 !important;
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: #58a6ff !important;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 class='omni-header'>OmniCortex</h1>", unsafe_allow_html=True)
st.markdown("<p class='omni-subheader'>Quant Committee • PSX & MUFAP</p>", unsafe_allow_html=True)
st.markdown("<p class='omni-tagline'>\"Ruthless Quantitative Analysis over Conversational Hype.\"</p>", unsafe_allow_html=True)

# Status Bar
st.markdown("""
<div class="status-bar">
    <span class="status-item"><span class="status-dot green"></span> BigQuery Connected</span>
    <span class="status-item"><span class="status-dot blue"></span> Gemini 3.1 Flash-Lite</span>
    <span class="status-item"><span class="status-dot purple"></span> Graham Protocol Active</span>
</div>
""", unsafe_allow_html=True)

# ----------------- CHAT UI / MEMORY SETUP -----------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "### 🏛️ OmniCortex Online\n\n"
                "The Investment Committee is assembled. All four seats are occupied.\n\n"
                "**Available Commands:**\n"
                "- `Analyze MEBL.KA` — Full 4-agent debate on Meezan Bank\n"
                "- `Analyze HUBC.KA` — Hub Power Company deep dive\n"
                "- `What's the KSE-100 doing today?` — Live macro scan\n"
                "- `[Any MUFAP Fund Name]` — Mutual fund Graham analysis\n\n"
                "State your query. The Committee awaits."
            )
        }
    ]

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ----------------- BRAIN LOADER -----------------
@st.cache_resource
def load_brain():
    from core_brain import get_omnicortex_brain
    return get_omnicortex_brain()

# ----------------- CHAT INPUT HANDLER -----------------
if prompt := st.chat_input("Query the Committee... (e.g., Analyze ENGRO.KA)"):
    # Display user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("⚙️ Committee in session — fetching SQL metrics and scanning live markets..."):
            try:
                brain = load_brain()
                
                # Build message list using simple dict format (no LangChain needed)
                chat_history = []
                for msg in st.session_state.messages[:-1]:
                    chat_history.append({
                        "role": msg["role"] if msg["role"] == "user" else "assistant",
                        "content": msg["content"]
                    })
                
                # Add the current user message
                chat_history.append({"role": "user", "content": prompt})
                
                # Invoke the brain
                response = brain.invoke({"messages": chat_history})
                
                ai_reply = response["messages"][-1].content
                st.markdown(ai_reply)
                
                # Save to session
                st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                
            except Exception as e:
                error_trace = traceback.format_exc()
                logger.error("OmniCortex crashed:\n%s", error_trace)
                st.error(f"⚠️ Pipeline Error: {str(e)}")
                st.markdown(f"**System Trace:**\n```\n{error_trace}\n```")
