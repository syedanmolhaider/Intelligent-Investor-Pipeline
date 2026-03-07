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
st.markdown("<p class='sub-header'>Benjamin Graham Value Investing Engine for the Pakistan Market (CrewAI + Groq)</p>", unsafe_allow_html=True)

# ----------------- CORE LOGIC -----------------
# 1. Input Section
user_query = st.text_input("Enter PSX Ticker (e.g., MEBL.KA) or MUFAP Fund Name:", placeholder="MEBL.KA")

@st.cache_data(ttl=3600)
def fetch_bq_data(identifier: str):
    client = bigquery.Client()
    if ".KA" in identifier.upper():
        query = f"SELECT * FROM `pk-market-data.market_data.graham_metrics_equities` WHERE Ticker = '{identifier.upper()}' ORDER BY Date DESC LIMIT 1"
    else:
        query = f"SELECT * FROM `pk-market-data.market_data.mufap_performance_metrics` WHERE Fund_Name LIKE '%{identifier}%' ORDER BY Date DESC LIMIT 1"
    
    return client.query(query).to_dataframe()

if user_query:
    with st.spinner("Fetching pre-computed Graham SQL metrics from BigQuery..."):
        try:
            df = fetch_bq_data(user_query)
            if df.empty:
                st.error("No metrics found in BigQuery. Please verify the ticker or fund name.")
            else:
                st.markdown("### 📊 Raw Pre-Calculated Quantitative Metrics")
                st.dataframe(df, use_container_width=True)
                
                # Check if we should trigger the AI
                if st.button("🧠 Analyze with Multi-Agent AI (CIO & Analyst)", type="primary"):
                    
                    st.markdown("### 💬 The Investment Committee Debate")
                    crew_expander = st.expander("Live Agent Thought Process & Real-Time Research", expanded=True)
                    
                    with crew_expander:
                        st.info("Initializing Llama 3 via Groq... Running multi-agent orchestration.")
                        try:
                            from run_crew import create_and_run_crew
                            
                            # Capture stdout (print statements) to show in UI
                            f = io.StringIO()
                            with redirect_stdout(f):
                                final_verdict = create_and_run_crew(user_query)
                            
                            log_output = f.getvalue()
                            st.text_area("Agent Output Logs", log_output, height=400)
                            
                        except ImportError as e:
                            logger.error("Missing libraries: %s", e)
                            st.error(f"Dependencies error: {e}")
                            st.warning("Note: When deployed to Streamlit Community Cloud, this will execute successfully from requirements.txt.")
                            final_verdict = "VERDICT UNAVAILABLE due to local Python missing CrewAI dependencies."
                        except Exception as e:
                            error_trace = traceback.format_exc()
                            logger.error("AI Assistant crashed with traceback:\n%s", error_trace)
                            st.error(f"Execution Error: {e}")
                            st.markdown(f"**Detailed AI Logger:**\n```python\n{error_trace}\n```")
                            final_verdict = "ERROR OCCURRED DURING ANALYSIS."
                            
                    st.markdown("### 🎯 Chief Investment Officer (CIO) Final Verdict")
                    st.markdown(f"<div class='cio-verdict'>{final_verdict}</div>", unsafe_allow_html=True)
                            
        except Exception as e:
            logger.exception("Database query failed:")
            st.error(f"Database connection error: {e}")
