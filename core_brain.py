import os
import json
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from tools import fetch_sql_metrics, search_live_news

SYSTEM_PROMPT = """You are OmniCortex, an elite, Wall Street-level quantitative AI assistant tailored for the Pakistan Stock Exchange (PSX) and Mutual Funds.
Your goal is to converse naturally with the user about their investments, the broader macroeconomic environment, and specific strategic plays.

You have access to powerful tools:
1. `fetch_sql_metrics`: Use this strictly when a user asks about a specific PSX Ticker (e.g., MEBL.KA, HUBC.KA) or a MUFAP Mutual Fund. It queries BigQuery for the absolute truth regarding Benjamin Graham value investing metrics. DO NOT guess metrics.
2. `search_live_news`: Use this to find real-time data on Pakistan's economy, the State Bank of Pakistan (SBP) interest rates, IMF bailouts, KSE-100 index data, or current news about a company. ALWAYS use this tool for any real-time market data. NEVER guess numbers.

If the user asks "I want to buy X", use your tools to analyze X, then give a highly analytical, conversational verdict (like a Chief Investment Officer would).
If the user asks a general question, just answer conversationally. Be concise, highly professional, and insightful.

**STRICT READABILITY RULES**:
1. NEVER output a wall of text.
2. Break up your response into VERY SHORT paragraphs (1-3 sentences max).
3. Use bullet points heavily.
4. Use **bolding** to highlight key data points and numbers.
5. Use line breaks aggressively to ensure the text breathes.
"""


class OmniCortexBrain:
    """
    A manually managed tool-calling agent that bypasses LangGraph entirely.
    This gives us absolute control over the Groq tool-calling loop,
    preventing XML hallucination errors.
    """

    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not found.")

        self.tools = [fetch_sql_metrics, search_live_news]
        self.tools_map = {tool.name: tool for tool in self.tools}

        # Bind tools DIRECTLY to the LLM via ChatGroq's native .bind_tools()
        # This ensures Groq receives a clean JSON schema, not XML hallucinations
        base_llm = ChatGroq(
            groq_api_key=api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0.0,
        )
        self.llm = base_llm.bind_tools(self.tools)

    def invoke(self, messages_input: dict) -> dict:
        """
        Runs a full conversation turn with automatic tool execution.
        Input: {"messages": [list of langchain messages]}
        Output: {"messages": [full message list including AI response]}
        """
        messages = list(messages_input["messages"])

        # Prepend system prompt if not already present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages.insert(0, SystemMessage(content=SYSTEM_PROMPT))

        # Tool-calling loop (max 5 iterations to prevent infinite loops)
        for _ in range(5):
            ai_response = self.llm.invoke(messages)
            messages.append(ai_response)

            # If the AI did NOT call any tools, we are done
            if not ai_response.tool_calls:
                break

            # Execute each tool call and append results
            for tool_call in ai_response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                if tool_name in self.tools_map:
                    try:
                        result = self.tools_map[tool_name].invoke(tool_args)
                    except Exception as e:
                        result = f"Tool execution error: {str(e)}"
                else:
                    result = f"Unknown tool: {tool_name}"

                # Append the tool result back as a ToolMessage
                messages.append(
                    ToolMessage(content=str(result), tool_call_id=tool_call["id"])
                )

            # Loop back so the LLM can process the tool results

        return {"messages": messages}


def get_omnicortex_brain():
    """Factory function that returns the OmniCortex brain instance."""
    return OmniCortexBrain()
