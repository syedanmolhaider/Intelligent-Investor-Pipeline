import os
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from tools import fetch_sql_metrics, search_live_news

def get_omnicortex_brain():
    """
    Initializes the OmniCortex Core Conversational Brain.
    Uses Llama-3.3-70b-versatile for top-tier tool calling and logical reasoning.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not found.")

    # We use ChatGroq directly here as the Core Chat Engine
    llm = ChatGroq(
        groq_api_key=api_key,
        model_name="llama-3.3-70b-versatile",
        temperature=0.3, # Slightly higher than 0.1 for natural conversation, but still accurate
    )

    # Bind the tools we already built for CrewAI
    tools = [fetch_sql_metrics, search_live_news]

    # Create the persona for OmniCortex
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are OmniCortex, an elite, Wall Street-level quantitative AI assistant tailored for the Pakistan Stock Exchange (PSX) and Mutual Funds.
Your goal is to converse naturally with the user about their investments, the broader macroeconomic environment, and specific strategic plays.

You have access to powerful tools:
1. `fetch_sql_metrics`: Use this strictly when a user asks about a specific PSX Ticker (e.g., MEBL.KA, HUBC.KA) or a MUFAP Mutual Fund. It queries BigQuery for the absolute truth regarding Benjamin Graham value investing metrics. DO NOT guess metrics. 
2. `search_live_news`: Use this to find real-time data on Pakistan's economy, the State Bank of Pakistan (SBP) interest rates, IMF bailouts, or current news about a company.

If the user asks "I want to buy X", use your tools to analyze X, then give a highly analytical, conversational verdict (like a Chief Investment Officer would).
If the user asks a general question, just answer conversationally. Be concise, highly professional, and insightful. 
Format your responses beautifully with Markdown (bolding, bullet points) so it is easy to read.
"""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Construct the Tool Calling Agent
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # Create an agent executor by passing in the agent and tools
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    return agent_executor
