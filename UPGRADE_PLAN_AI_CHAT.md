# OmniCortex Upgrade Plan: Conversational AI Search Engine
**Status**: Planning Phase
**Goal**: Transform the Intelligent Investor Pipeline from a static, form-based dashboard into a highly intelligent, conversational AI search engine (similar to ChatGPT/Gemini) tailored for Pakistani financial markets.

---

## Phase 1: Frontend UI Transformation (The Chat Interface)
We will completely overhaul the Streamlit interface to reflect a premium, state-of-the-art conversational engine.
- **Remove static inputs**: Delete the rigid `st.text_input` and dropdowns.
- **Implement Chat UI**: Utilize Streamlit's native `st.chat_input()` and `st.chat_message()` components.
- **Conversational Memory**: Implement `st.session_state.messages` to store the history of the conversation, allowing the AI to remember what you discussed earlier in the session.
- **Premium Aesthetics**: Apply custom CSS to give the app a dark-mode, glassmorphism, high-tech vibe matching the "OmniCortex" name.

## Phase 2: Building the OmniCortex Core Brain (Intelligent Router)
Currently, the system rigidly fires 4 agents in a sequence every time you press a button. We need a dynamic "Core Brain" that actually *talks* to you and decides what to do based on your input.
- **The Core Agent**: We will create a primary conversational agent powered by the **Groq Llama 3.3 70B** model.
- **System Prompting**: Give it a persona. It will act as a highly elite, Wall Street-level quantitative AI assistant.
- **Dynamic Intent Recognition**: When you type:
  - *"How is the market going?"* → It will naturally summarize general knowledge or trigger the news tool.
  - *"I want to buy MEBL, what do you think?"* → It will recognize the intent to analyze an asset and dynamically trigger the data fetch tools or the Crew.
  - *"If I sold HUBC today, what should I reinvest in?"* → It will hold a natural conversation about portfolio strategy.

## Phase 3: Dynamic Tool Integration
We will bind our existing backend capabilities directly to the OmniCortex Core Brain.
- Instead of CrewAI running sequentially in a rigid box, we will expose `fetch_sql_metrics` and `search_live_news` as **Functions** to the Core Conversational Agent.
- The AI will autonomously decide *when* to use BigQuery and *when* to search DuckDuckGo based on the natural flow of your conversation.

## Phase 4: Streaming & Streaming Responses
- To make it feel like ChatGPT, we will implement response streaming. Instead of waiting 30 seconds for a massive block of text to instantly appear, the AI will type its response out to you in real-time.

---

### Step 1 Execution Start
To begin, I will overhaul `app.py`. I will strip out the old UI and implement the conversational Chat UI with a sleek custom CSS design. Are you ready to begin?
