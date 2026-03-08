# 🏛️ Intelligent Investor AI (OmniCortex) - Project Structure & Workflow

OmniCortex is an autonomous, conversational **AI Quantitative Investment Committee** tailored explicitly for the **Pakistan Stock Exchange (PSX)** and the **Mutual Funds Association of Pakistan (MUFAP)**. It ingests daily market data, calculates Benjamin Graham's value investing metrics, and leverages a "Council of Personas" to debate out an asset's worth before delivering a final investment verdict to the user.

---

## 🏗️ High-Level Architecture

The project consists of three major tiers:
1. **Frontend (UI Layer)**: A sleek, dark-themed interface built in Streamlit that parses strict JSON payloads into modular components.
2. **AI Intelligence Engine**: A custom sequential, multi-agent pipeline powered by Google's **Gemini 2.5 Flash**.
3. **Data Pipelines & Storage**: Python-based scheduled scrapers and API fetchers that push raw market equity, NAV data, and dynamic macro indicators directly to **Google BigQuery** for high-speed querying.

---

## 📂 Core Project Structure

### 1. Presentation & Application Layer
- **`app.py`**
  - The main entry point to the system.
  - Implements the UI using Streamlit, parsing strict JSON responses from the AI into modular metric cards.
  - Handles UI component styling (CSS rendering for inputs, text, and verdicts).
  - Handles authentication resolution (loading `bq-key.json` or Streamlit Cloud Secrets).
  - Instantiates the `OmniCortexBrain` (from `core_brain.py`) and passes the chat history securely.

### 2. The AI "Brain" (Logic Layer)
- **`core_brain.py`**
  - Contains the core logic for the **Sequential Multi-Agent Pipeline**, isolating LLM operations into discrete functional blocks.
  - Features aggressive Regex input sanitization to strip parentheses and artifacts before BigQuery insertion.
  - **The 4-Stage Agent Pipeline**:
    - *Agent 1 (Graham)*: Dedicated solely to querying foundational fundamentals via SQL. Returns raw fundamental context.
    - *Agent 2 (Macro)*: Scans the web simultaneously or immediately after for macroeconomic systemic conditions.
    - *Agent 3 (Risk)*: Combines the context of Graham and Macro, outputting explicit downside risks and liquidity traps without using external tools.
    - *Agent 4 (CIO)*: Takes the previous context and enforces strict JSON synthesis (`response_schema`), rendering a final Verdict (`BUY`, `HOLD`, `SELL`, or `ERROR`). Governed by strict anti-hallucination protocols rejecting verdicts if underlying data is empty.
  - **Tools**: Defines standard tools that Gemini natively calls to ground its analysis:
    - `fetch_sql_metrics(asset_identifier)`: Queries historical/valuation inputs dynamically from BigQuery. Features a 48-hour data freshness circuit breaker.
    - `search_live_news(search_query)`: Wraps DuckDuckGo to browse live headlines and market sentiment on the fly.

### 3. Data Pipelines (ETL)
Data generation flows run autonomously, pulling raw data and uploading it securely for the AI to analyze later.

- **`mufap_pipeline.py`**
  - Connects to MUFAP's live data portal (specifically targeting the `IndustryStatDaily` table).
  - Uses `cloudscraper` and `pandas` to sidestep anti-bot protections.
  - Cleans HTML structures and ingests standard columns (Date, Fund_Name, Category, NAV).
  - Validates and streams output continuously into the `pk-market-data.market_data.mufap_daily_nav` BigQuery table via write-append.
  - Features robust `try/except` guardrails triggering local Python logging (`etl_errors.log`) upon scraper or formatting failure.

- **`market_pipeline.py`**
  - Connects out to TradingView (via the undocumented `tvDatafeed` Python library).
  - Fetches the closing price and volume for PSX indices (e.g., KSE100) and specific equities (e.g., MEBL).
  - Massages this historical bar data and forwards it directly to the `pk-market-data.market_data.psx_daily_equities` BigQuery table.
  - Also features aggressive try/except local Python logging.

### 4. Database Views & Transformations
- **`create_mufap_view.py`**
  - This script recreates the `mufap_performance_metrics` SQL View.
  - It utilizes SQL window functions and complex LEFT JOINS against older timestamp bounds (`DATE_SUB`) to dynamically calculate Week-over-Week (WoW), Month-over-Month (MoM), and Annualized returns off the raw NAV data.
  - **Dynamic Graham Filter**: Instead of a hardcoded rate, cross-joins against the dynamic `macro_indicators` BigQuery table to determine if an asset's annualized yield functionally defeats the live State Bank of Pakistan Risk-Free Rate.

### 5. Utilities & Diagnostics
- **`update_macro.py`**: A deployment utility strictly designed to map and update sweeping macroeconomic metrics (like the SBP Policy Rate) into the BigQuery ecosystem to maintain dynamic SQL views.
- **`inject_history.py`**: Manual script used to populate BigQuery with mocked or historical data strings (used to trigger MoM and WoW math formulas when tracking brand new fund inception).
- **`debug_mufap.py` / `test_sarmaaya.py` / `test_agent.py`**: A suite of one-off scripts used specifically for testing third party scrapers, APIs, index statuses, or model responses without booting up the full Chat UI.

---

## 🔄 The Complete Action Workflow (Step-by-Step)

Here is exactly what happens linearly when you ask: **"Analyze NBP Islamic Stock Fund (NBPI SF)"** or **"MEBL.KA"**:

1. **User input recorded**: You type a query in Streamlit via `app.py`.
2. **Context Packaged**: Your chat history is serialized and passed off to `OmniCortexBrain`.
3. **Regex Sanitization**: Parenthetical tickers are stripped aggressively (e.g. `(NBPI SF)` is excised to appease strict BigQuery matching).
4. **Agent 1 (Graham)**: Fetches raw data from BigQuery via automatic function calling. If data is stale (>48 hours), explicitly errors out.
5. **Agent 2 (Macro)**: Triggers DuckDuckGo to browse for macroeconomic context and live news.
6. **Agent 3 (Risk)**: Absorbs data linearly from Agents 1 & 2. Forms a vulnerability mapping without using external queries.
7. **Agent 4 (CIO Synthesis)**: Enforces `response_schema` generation configuration. Translates internal analysis into a strict JSON payload. Immediately returns `ERROR / INSUFFICIENT DATA` if Agent 1 returned zero metrics.
8. **Finalization & Formatting**: `app.py` catches the CIO JSON payload, strips the JSON string, and populates Streamlit dashboard visualization UI components synchronously.

---

## 🔒 Security & Deployment Specs
- **Credentials**: Google Cloud authentication is rigorously checked on boot in `app.py`. It falls back recursively from local environment variables (`bq-key.json`) up into Streamlit secrets.
- **Dependency Management**: Standardized via `requirements.txt`.
- **System Constraints**: The AI is hardwired (via `Anti-Drift Protocol`) to refuse manual math calculation, force execution of its tool queries before any responses are populated, and NEVER exhibit standard chatbot platitudes ("Sure!", "I'd be happy to...").
