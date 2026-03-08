# MASTER PROJECT PLAN: OmniCortex DNA — AI Quant Committee for Pakistan Markets

## 1. Executive Summary & Core Doctrine
This project is an autonomous AI investment committee for the Pakistani market (PSX Equities and MUFAP Mutual Funds), powered by Google Gemini 3.1 Flash-Lite.

**The Doctrine:** "Ruthless Quantitative Analysis over Conversational Hype."  
Analysis is governed strictly by Benjamin Graham's *The Intelligent Investor* principles — low P/E, low P/B, high dividend yields near 52-week lows, and an absolute demand for a margin of safety.

**The Lifestyle Context:** The user works a night shift (7:30 PM to 3:30 AM PKT). All automated data pipelines finish by 5:00 PM PKT daily.

---

## 2. The Three Non-Negotiable Pillars

### Pillar 1: Zero Math Hallucination
The AI is **strictly forbidden** from calculating financial ratios, moving averages, or intrinsic values. It acts solely as an **Interpreter** of data fetched from Google BigQuery.

### Pillar 2: The Graham Doctrine
All analysis filters through Benjamin Graham's "Margin of Safety." We value low-PE, low-PB, and high-dividend yields near 52-week lows.

### Pillar 3: The Anti-Chatbot Protocol
OmniCortex is NOT a virtual assistant. It is a **Quant Committee**. No pleasantries. No vague summaries. It speaks ONLY in the 4-Agent Debate format.

---

## 3. Infrastructure Architecture (The Google Stack)

| Component | Technology | Details |
|-----------|-----------|---------|
| **Database** | Google BigQuery | Project: `pk-market-data` |
| **LLM Engine** | Gemini 3.1 Flash-Lite | Model: `gemini-3.1-flash-lite-preview` |
| **Orchestrator** | Google Generative AI SDK | Native Python SDK |
| **Tool Calling** | Automatic Function Calling | Built-in SDK feature |
| **Live Search** | DuckDuckGo Search | No API key required |
| **Frontend** | Streamlit | Community Cloud hosted |
| **Automation** | GitHub Actions | Daily cron at 5 PM PKT |

### What Was Removed:
- ❌ CrewAI — Replaced by native Gemini function calling
- ❌ LangChain — No longer needed; plain dicts replace message objects
- ❌ Groq/Llama — Replaced by Gemini 3.1 Flash-Lite
- ❌ Regex Sanitizers — Gemini handles JSON/XML cleanup natively

---

## 4. The 4-Agent Committee Protocol

Every analysis triggers a structured debate between these four personas:

### 👔 Persona 1: The Graham Analyst (Fundamentalist)
- **Goal:** Protect Capital
- **Behavior:** Only cares about SQL metrics. Ignores news. Demands to know if the asset is "cheap" relative to its history.

### 🌍 Persona 2: The Macro Expert (News)
- **Goal:** Contextualize the Moment
- **Behavior:** Reads DuckDuckGo results. Connects SBP rates, IMF news, and KSE-100 to the ticker.

### 🕵️ Persona 3: The Risk Skeptic (Contrarian)
- **Goal:** Destroy the Thesis
- **Behavior:** Must actively argue against the others. Looks for value traps, liquidity issues, political instability.

### ⚖️ Persona 4: The Chief Investment Officer (CIO)
- **Goal:** Finality
- **Behavior:** Weighs the conflict. Issues one bolded verdict: **BUY ON CHEAP**, **HOLD / WAIT**, or **SELL**.

---

## 5. Prompt Hierarchy (4 Layers)

To prevent "Recency Bias" where the model drifts into chatbot behavior:

1. **Layer 1 — Identity:** Who is OmniCortex. The Graham Doctrine.
2. **Layer 2 — Tool Specs:** How to use `fetch_sql_metrics` and `search_live_news`.
3. **Layer 3 — Formatting:** The mandatory Debate Transcript output format.
4. **Layer 4 — System Override:** Anti-drift protocol ensuring no polite chatbot behavior.

---

## 6. Execution Roadmap & Status Tracker

### PHASE 0: Ground Base [STATUS: ✅ COMPLETED]
- [x] Local Env: Windows, Python `venv` active
- [x] Database: BigQuery Project (`pk-market-data`), Dataset (`market_data`) created
- [x] Authentication: `bq-key.json` secured locally

### PHASE 1: Data Extraction Pipelines [STATUS: ✅ COMPLETED]
- [x] PSX Script (`market_pipeline.py`): Daily closing data → BigQuery
- [x] MUFAP Script (`mufap_pipeline.py`): Bypasses firewalls via `cloudscraper` → BigQuery

### PHASE 2: Cloud Automation [STATUS: ✅ COMPLETED]
- [x] GitHub Actions cron job (Mon-Fri, 5 PM PKT)
- [x] `requirements.txt` generated
- [x] GCP_CREDENTIALS secret configured

### PHASE 3: SQL Logic Engine [STATUS: ✅ COMPLETED]
- [x] `graham_metrics_equities` BigQuery View (52-week, SMAs, volume)
- [x] `mufap_performance_metrics` BigQuery View (NAV growth, vs. SBP rate)

### PHASE 4: OmniCortex Brain (Gemini 3.1) [STATUS: ✅ COMPLETED]
- [x] Migrated from CrewAI/Groq to native Gemini SDK
- [x] Implemented 4-layer prompt hierarchy
- [x] Automatic Function Calling (no regex/sanitizers)
- [x] Parameterized SQL queries (injection protection)
- [x] 4-Agent Debate format enforced via system prompt

### PHASE 5: Frontend Dashboard [STATUS: ✅ COMPLETED]
- [x] Streamlit chat UI with premium dark theme
- [x] Status indicators (BigQuery, Gemini, Graham Protocol)
- [x] LangChain dependency removed
- [x] Session-based conversation memory
- [ ] **Step 5.3: Deployment** — Deploy to Streamlit Community Cloud

---

## 7. File Reference

| File | Purpose |
|------|---------|
| `core_brain.py` | The OmniCortex Brain — Gemini 3.1, tools, system prompt, 4-agent protocol |
| `app.py` | Streamlit frontend — chat UI, auth, session memory |
| `tools.py` | Standalone tool testing module |
| `crew_logic.py` | Utility LLM initializer (legacy compatibility) |
| `market_pipeline.py` | PSX data extraction → BigQuery |
| `mufap_pipeline.py` | MUFAP data extraction → BigQuery |
| `bq-key.json` | BigQuery service account key (gitignored) |
| `requirements.txt` | Python dependencies |

---

## 8. Transition Notes: From Groq/Llama to Gemini 3.1

- **Sanitizers Deleted:** Gemini handles JSON/XML cleanup natively
- **Native Context:** Gemini's 1M+ token context window allows entire session histories
- **Search Depth:** `max_results=10` for web searches to ensure sufficient material
- **Cost:** Flash-Lite tier is optimized for speed and minimal cost