# MASTER PROJECT PLAN: Intelligent Investor Pakistan Market AI

## 1. Executive Summary & User Mindset
This project is a fully automated, multi-agent AI financial dashboard tailored for the Pakistani market (PSX Equities and MUFAP Mutual Funds). 
**The Mindset:** We do not chase hype. The core logic is strictly governed by Benjamin Graham’s "The Intelligent Investor" principles—finding undervalued assets, demanding a margin of safety, and calculating intrinsic value. 
**The Lifestyle Context:** The user works a night shift (7:30 PM to 3:30 AM PKT). Therefore, all automated data pipelines MUST finish processing by 5:00 PM PKT every day. When the user sits down for work, the dashboard must already hold the fully processed daily numbers.

## 2. Strict Constraints & Philosophy
* **Budget:** $0. MUST be 100% FREE for the first year. We use open-source tools, free cloud tiers (BigQuery Sandbox), and generous API tiers (Groq) to avoid costs. 
* **Zero Manual Intervention:** Once deployed, the pipeline must run silently in the background. The user simply inputs a ticker/fund into the UI, and the system does the rest.
* **Accuracy Over AI Guesses:** LLMs are notorious for hallucinating math. **Rule:** AI agents will NEVER calculate standard deviations, moving averages, or Graham formulas from raw data. All math is pre-computed in SQL via BigQuery Views. The AI only reads the final metrics.
* **Contextual Awareness (Pakistan Macro):** The system must compare returns against the current State Bank of Pakistan (SBP) interest rate and local inflation. An asset is only "cheap" if its real return beats the local risk-free rate.

## 3. Architecture & Tech Stack
* **Data Extraction:** Python, `yfinance` (PSX), `cloudscraper` (MUFAP), `pandas`.
* **Database:** Google Cloud BigQuery (Sandbox Free Tier).
* **Automation:** GitHub Actions (Cron Jobs).
* **AI Framework:** CrewAI (Python) for multi-agent orchestration.
* **LLM Engine:** Groq API (Running Meta's Llama 3 models for high-speed, free inference).
* **Live World Knowledge:** `duckduckgo-search` library (Free, no-API-key web scraping for geopolitical/macro news).
* **Frontend:** Streamlit Community Cloud.

---

## 4. Execution Roadmap & Status Tracker

### PHASE 0: Ground Base [STATUS: COMPLETED]
* [x] **Local Env:** Windows, Python `venv` active.
* [x] **Database:** BigQuery Project (`pk-market-data`), Dataset (`market_data`) created. Tables `psx_daily_equities` and `mufap_daily_nav` are live.
* [x] **Authentication:** `bq-key.json` secured locally and in `.gitignore`.

### PHASE 1: Data Extraction Pipelines [STATUS: COMPLETED]
* [x] **PSX Script (`market_pipeline.py`):** Pulls daily closing data and appends to BigQuery.
* [x] **MUFAP Script (`mufap_pipeline.py`):** Bypasses MUFAP firewalls using `cloudscraper`, standardizes columns, and appends to BigQuery.

### PHASE 2: Cloud Automation [STATUS: COMPLETED]
* **Goal:** Automate the daily data scrape so it runs flawlessly before the user's night shift.
* [x] **Step 2.1: Generate `requirements.txt`:** The agent must scan the python files and generate a comprehensive requirements file including `pandas`, `google-cloud-bigquery`, `cloudscraper`, `yfinance`, `html5lib`, `db-dtypes`.
* [x] **Step 2.2: GitHub Secrets Setup:** The agent must provide the user explicit, click-by-click instructions on how to take the local `bq-key.json` file and save its contents as a repository secret named `GCP_CREDENTIALS` in GitHub.
* [x] **Step 2.3: GitHub Actions YAML (`.github/workflows/daily_scrape.yml`):** * Must run on `ubuntu-latest`.
    * **Cron Schedule:** `0 12 * * 1-5` (Runs Monday-Friday at 12:00 UTC, which is 5:00 PM PKT).
    * **Steps:** Check out code -> Set up Python 3.10 -> Install `requirements.txt` -> Reconstruct `bq-key.json` from the GitHub Secret -> Run `market_pipeline.py` -> Run `mufap_pipeline.py`.

### PHASE 3: The SQL Logic Engine (Pre-computation) [STATUS: COMPLETED]
* **Goal:** Build the Benjamin Graham mathematical filters directly inside BigQuery to prevent LLM hallucination.
* [x] **Step 3.1: Equities Graham View:** The agent must write a BigQuery standard SQL script to create a View (e.g., `graham_metrics_equities`). It should calculate: 
    * 52-week high/low proximity (is it on sale?).
    * 50-day and 200-day Simple Moving Averages (SMA).
    * Volume trend anomalies.
* [x] **Step 3.2: Mutual Funds View:** The agent must write a SQL View (e.g., `mufap_performance_metrics`) that calculates:
    * Rolling week-over-week and month-over-month NAV growth.
    * Comparison of the annualized return against a baseline 22% SBP Risk-Free rate.
* *(Note: Provided the exact SQL code and successfully ran it via python `create_mufap_view.py`).*

### PHASE 4: The Multi-Agent AI Brain (CrewAI) [STATUS: COMPLETED]
* **Goal:** Build the intelligence layer using free open-source models via Groq.
* [x] **Step 4.1: CrewAI Initialization:** Create `crew_logic.py`. Initialize the Groq LLM client (using the `GROQ_API_KEY` environment variable). Implement rate-limit delays if necessary to respect Groq's free tier.
* [x] **Step 4.2: Tool Creation:** Create a custom CrewAI tool that queries BigQuery using the Views created in Phase 3. Create a second tool using DuckDuckGo search for live news.
* [x] **Step 4.3: Define Personas:**
    * **The Graham Analyst:** Strict, numbers-driven. Only cares about the SQL metrics. Writes the base thesis.
    * **The Macro Expert:** Uses the web search tool to find live news about Pakistan's economy, IMF bailouts, or global oil prices.
    * **The Risk Skeptic:** A contrarian agent specifically prompted to find flaws, regulatory risks, or market traps in the Analyst's thesis.
    * **The Chief Investment Officer (CIO):** The final decider. Synthesizes the debate into a simple, actionable verdict: "Buy on Cheap", "Hold/Wait for a drop", or "Sell".
* [x] **Step 4.4: Task Orchestration:** Link the agents sequentially so the output of one feeds the next.

### PHASE 5: The Frontend Dashboard [STATUS: PENDING]
* **Goal:** A clean, minimal UI hosted for free.
* [x] **Step 5.1: Build `app.py`:** Use Streamlit. 
* [x] **Step 5.2: UI Flow:** 1. A search bar for the user to input a PSX Ticker or MUFAP Fund Name.
    2. A data table showing the raw, pre-computed SQL metrics (Margin of safety, moving averages).
    3. An "Analyze with AI" button.
    4. An expander showing the live conversation/debate between the CrewAI agents.
    5. A final, bolded alert/verdict from the CIO agent.
* [ ] **Step 5.3: Deployment:** Provide instructions on linking the GitHub repo to Streamlit Community Cloud for free hosting.

---

## 5. Instructions for the AI Agent (Antigravity)
When the user asks you to "proceed to the next step," you MUST follow these rules:
1. **Read & Check:** Read this entire `MASTER_PLAN.md` file. Find the FIRST sub-step marked as `[STATUS: PENDING]`.
2. **Isolate Focus:** Do NOT attempt to execute multiple sub-steps at once. If Step 2.1 is pending, only do Step 2.1.
3. **Execute & Explain:** Write the required code. Provide explicitly clear, step-by-step instructions on where the user should paste the code or what buttons they need to click in their browser.
4. **Wait for Confirmation:** End your response by asking the user to confirm if the step worked. Do not proceed to the next step until the user says "done" or "successful".