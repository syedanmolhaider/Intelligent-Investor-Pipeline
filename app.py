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
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500&display=swap');

    /* ============ CORE DARK THEME ============ */
    .stApp {
        background: #0a0a0a !important; /* Deep space black */
        color: #e6edf3 !important;
        font-family: 'Roboto Mono', monospace !important;
    }

    /* ============ HEADER STYLING ============ */
    .omni-header {
        font-family: 'Orbitron', sans-serif;
        font-size: 3.5rem;
        font-weight: 700;
        text-align: center;
        background: linear-gradient(135deg, #00ffcc 0%, #0abfbc 40%, #ff00ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-top: 1.5rem;
        margin-bottom: 0px;
        letter-spacing: 2px;
        text-shadow: 0 0 10px rgba(0, 255, 204, 0.4);
    }

    .omni-subheader {
        font-family: 'Roboto Mono', monospace;
        color: #00ffcc;
        text-align: center;
        margin-bottom: 0.5rem;
        font-size: 0.85rem;
        font-weight: 500;
        letter-spacing: 3px;
        text-transform: uppercase;
    }

    .omni-tagline {
        font-family: 'Roboto Mono', monospace;
        color: #aaaaaa;
        text-align: center;
        margin-bottom: 3rem;
        font-size: 0.8rem;
        font-style: italic;
    }

    /* ============ STATUS INDICATOR ============ */
    .status-bar {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin-bottom: 2rem;
        padding: 0.6rem 1.5rem;
        background: rgba(17, 17, 17, 0.8);
        border: 1px solid #00ffcc;
        border-radius: 8px;
        box-shadow: 0 0 10px rgba(0, 255, 204, 0.2);
        max-width: 600px;
        margin-left: auto;
        margin-right: auto;
    }

    .status-item {
        font-family: 'Orbitron', sans-serif;
        font-size: 0.75rem;
        color: #dddddd;
        display: flex;
        align-items: center;
        gap: 0.4rem;
        letter-spacing: 1px;
    }

    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }

    .status-dot.green { background: #39ff14; box-shadow: 0 0 8px #39ff14; }
    .status-dot.blue { background: #00ffcc; box-shadow: 0 0 8px #00ffcc; }
    .status-dot.purple { background: #ff00ff; box-shadow: 0 0 8px #ff00ff; }

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
        font-family: 'Roboto Mono', monospace !important;
        font-size: 1rem !important;
        line-height: 1.6 !important;
        color: #ffffff !important;
        font-weight: 400 !important;
    }

    .stChatMessage .stMarkdown li {
        font-family: 'Roboto Mono', monospace !important;
        font-size: 0.95rem !important;
        line-height: 1.5 !important;
        color: #cccccc !important;
        margin-bottom: 0.5rem;
    }

    .stChatMessage .stMarkdown strong {
        color: #00ffcc !important;
        font-weight: 600 !important;
    }

    .stChatMessage .stMarkdown h3 {
        font-family: 'Orbitron', sans-serif !important;
        color: #00ffcc !important;
        font-size: 1.3rem !important;
        border-bottom: 1px solid rgba(0, 255, 204, 0.3);
        padding-bottom: 0.5rem;
        margin-top: 1.5rem;
        text-shadow: 0 0 5px rgba(0, 255, 204, 0.5);
    }

    /* Persona section styling */
    .stChatMessage .stMarkdown h3 + p strong:first-child {
        color: #ff00ff !important;
    }

    /* Code blocks in chat (for error traces) */
    .stChatMessage .stMarkdown code {
        font-family: 'Roboto Mono', monospace !important;
        background: rgba(17, 17, 17, 0.9) !important;
        color: #39ff14 !important;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.85rem;
        border: 1px solid #333;
    }

    /* Chat Input Bar and Bug Fix */
    [data-testid="stChatInput"] {
        border-radius: 8px !important;
        border: 1px solid #00ffcc !important;
        box-shadow: 0 0 15px rgba(0, 255, 204, 0.2) !important;
        background: #111111 !important;
    }

    /* Fix for invisible text in Streamlit input */
    div[data-testid="stChatInput"] textarea, [data-testid="stChatInput"] textarea::placeholder {
        font-family: 'Roboto Mono', monospace !important;
        font-size: 1rem !important;
        color: #00ffcc !important; 
        -webkit-text-fill-color: #00ffcc !important;
        background-color: transparent !important;
    }
    
    [data-testid="stChatInput"] svg {
        fill: #ff00ff !important;
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
        if message["role"] == "assistant":
            try:
                payload = json.loads(message["content"])
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown("### 🏛️ Committee Synthesis")
                        st.info(f"**Graham Analysis:** {payload.get('graham_analysis')}")
                        st.warning(f"**Macro Analysis:** {payload.get('macro_analysis')}")
                        st.error(f"**Risk Assessment:** {payload.get('risk_assessment')}")
                    with col2:
                        verdict = payload.get('verdict', 'HOLD').upper()
                        v_color = "#3fb950" if "BUY" in verdict else ("#f85149" if "SELL" in verdict else "#d29922")
                        st.markdown(f'''
                        <div style="background: rgba(22, 27, 34, 0.8); padding: 20px; border-radius: 10px; border: 1px solid #30363d; text-align: center;">
                            <h4 style="color: #8b949e; margin-bottom: 5px; font-family: 'JetBrains Mono', monospace;">VERDICT</h4>
                            <h2 style="color: {v_color}; margin: 0; font-family: 'Inter', sans-serif;">{verdict}</h2>
                            <hr style="border-color: #30363d; margin: 15px 0;">
                            <h4 style="color: #8b949e; margin-bottom: 5px; font-family: 'JetBrains Mono', monospace;">CONFIDENCE</h4>
                            <h2 style="color: #58a6ff; margin: 0; font-family: 'Inter', sans-serif;">{payload.get('confidence_score')}%</h2>
                        </div>
                        ''', unsafe_allow_html=True)
            except json.JSONDecodeError:
                st.markdown(message["content"])
        else:
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
                
                try:
                    payload = json.loads(ai_reply)
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown("### 🏛️ Committee Synthesis")
                            st.info(f"**Graham Analysis:** {payload.get('graham_analysis')}")
                            st.warning(f"**Macro Analysis:** {payload.get('macro_analysis')}")
                            st.error(f"**Risk Assessment:** {payload.get('risk_assessment')}")
                        with col2:
                            verdict = payload.get('verdict', 'HOLD').upper()
                            v_color = "#3fb950" if "BUY" in verdict else ("#f85149" if "SELL" in verdict else "#d29922")
                            st.markdown(f"""
                            <div style="background: rgba(22, 27, 34, 0.8); padding: 20px; border-radius: 10px; border: 1px solid #30363d; text-align: center;">
                                <h4 style="color: #8b949e; margin-bottom: 5px; font-family: 'JetBrains Mono', monospace;">VERDICT</h4>
                                <h2 style="color: {v_color}; margin: 0; font-family: 'Inter', sans-serif;">{verdict}</h2>
                                <hr style="border-color: #30363d; margin: 15px 0;">
                                <h4 style="color: #8b949e; margin-bottom: 5px; font-family: 'JetBrains Mono', monospace;">CONFIDENCE</h4>
                                <h2 style="color: #58a6ff; margin: 0; font-family: 'Inter', sans-serif;">{payload.get('confidence_score')}%</h2>
                            </div>
                            """, unsafe_allow_html=True)
                            
                except json.JSONDecodeError:
                    st.markdown(ai_reply)
                
                # Save to session
                st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                
            except Exception as e:
                error_trace = traceback.format_exc()
                logger.error("OmniCortex crashed:\n%s", error_trace)
                st.error(f"⚠️ Pipeline Error: {str(e)}")
                st.markdown(f"**System Trace:**\n```\n{error_trace}\n```")
