# OmniCortex Changelog

## [V2.2] - 2026-03-08 (Localization & Sci-Fi UI Overhaul)

### Changed
- **System Prompt Localization**: Rewrote the internal system instructions for Graham, Macro, Risk, and CIO agents to exclusively output text inside Layman's Roman Urdu using common analogies. Strictly preserved English formatting for JSON string keys and the overarching CIO `verdict` for UI stability.
- **Sci-Fi UI Redesign**: Overhauled `app.py` UI containers. Migrated primary typography to `Orbitron` and `Roboto Mono`. Reassigned application background to deep-space black (`#0a0a0a`) and added neon-cyan (`#00ffcc`) and magenta (`#ff00ff`) glowing bounds around metrics using CSS `box-shadow`.

### Fixed
- **UI Input Bug**: Injected CSS override for `div[data-testid="stChatInput"] textarea` targeting the `color` and `-webkit-text-fill-color` attributes preventing text field keystrokes from rendering invisibly.

## [V2.1] - 2026-03-08 (Bug Fixes & Logic Hardening)

### Changed
- **AWS Dependencies Excised**: Removed `boto3` and AWS SNS push notification logic from `market_pipeline.py` and `mufap_pipeline.py` to prevent fatal `NoCredentialsError` crashes. Replaced with standard local Python logging (`etl_errors.log`).
- **CIO Fallback Logic (Anti-Hallucination)**: Updated the System Prompt for Agent 4 (CIO). Added a critical rule explicitly instructing the CIO to immediately halt analysis and return an `ERROR / INSUFFICIENT DATA` verdict if Agent 1 (Graham) fails to find foundational data or returns zero metrics.

### Added
- **Input Sanitization**: Introduced a pre-processing Regex step in `core_brain.py` `invoke()` method. Now strictly strips parenthetical statements and trailing spaces (e.g., `"NBP Islamic Stock Fund (NBPI SF)"` becomes `"NBP Islamic Stock Fund"`) to ensure correct BigQuery string matching.

---

## [V2.0] - 2026-03-08 (Multi-Agent Architecture & Pipeline Hardening)

### Changed
- **Multi-Agent Architecture**: Decoupled the monolithic single-prompt loop into a sequential pipeline of four isolated agents (Graham, Macro, Risk, CIO) inside `core_brain.py`.
- **Strict Output Schemas**: Disabled open-ended text generations. Agent 4 (CIO) enforced to use Gemini's `response_schema` directly, outputting predictable JSON payloads (`graham_analysis`, `macro_analysis`, `risk_assessment`, `verdict`, and `confidence_score`).
- **Streamlit UI**: Updated `app.py` to parse the JSON format and render strict cleanly-styled graphical reporting components instead of chat bubbles.
- **Dynamic Macro Integration**: Replaced the hardcoded 22% rate within the BigQuery Vue query (`create_mufap_view.py`) with a dynamic `CROSS JOIN` reference pulling live rates from a new table.

### Added
- **Data Freshness Circuit Breakers**: Modified the `fetch_sql_metrics` function to intercept the BigQuery SQL `Date` attribute. Analyzes timestamp; triggers explicit structural abort (`ERROR: DATA STALE`) if trailing the current date by > 48 hours.
- **AWS SNS Notifications (Deprecated in V2.1)**: Initially wrapped `mufap_pipeline.py` and `market_pipeline.py` in `try/except` guardrails triggering immediate push notifications for failure broadcasts. 
- **Macro Table Initialization**: Added a script (`update_macro.py`) designed to routinely update macroeconomic metrics (like the `SBP_Policy_Rate`) locally inside the newly mapped `pk-market-data.market_data.macro_indicators` BigQuery table.
