from crewai import Agent, Task, Crew, Process
from crew_logic import initialize_llm
from tools import fetch_sql_metrics, search_live_news

def create_and_run_crew(asset_or_fund: str):
    llm = initialize_llm()
    if not llm:
        return "Error: LLM could not be initialized. Check API Key."

    # 1. The Graham Analyst
    graham_analyst = Agent(
        role='The Benjamin Graham Quantitative Analyst',
        goal=f'Analyze the intrinsic value, margin of safety, and moving averages for {asset_or_fund} strictly based on SQL database metrics.',
        backstory='You are a strict disciple of Benjamin Graham. You ignore market hype, P/E anomalies due to sentiment, and focus purely on absolute numbers: 52-week lows, moving averages, and volume spikes. You demand a margin of safety.',
        verbose=True,
        allow_delegation=False,
        tools=[fetch_sql_metrics],
        llm=llm
    )

    # 2. The Macro Expert
    macro_expert = Agent(
        role='Pakistan Macro-economic Expert',
        goal=f'Find live, real-time news regarding Pakistan\'s economy, SBP interest rates, and specific news about {asset_or_fund} to contextualize the quantitative data.',
        backstory='You are a seasoned economist in Karachi. You know that no asset is cheap if the country is defaulting or interest rates are at 22%. You scrape the web for the latest updates on inflation, IMF, and specific company/fund news.',
        verbose=True,
        allow_delegation=False,
        tools=[search_live_news], 
        llm=llm
    )

    # 3. The Risk Skeptic
    risk_skeptic = Agent(
        role='The Contrarian Risk Skeptic',
        goal='Find the hidden traps, regulatory risks, and flaws in the Analyst and Macro Expert\'s thesis.',
        backstory='You are naturally pessimistic. When others see a "cheap" stock, you assume it is a value trap. You look for reasons why the asset might go to zero or underperform the risk-free rate.',
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    # 4. The Chief Investment Officer (CIO)
    cio = Agent(
        role='Chief Investment Officer',
        goal='Synthesize the quantitative data, macro context, and risk skepticism into a final, actionable 1-paragraph investment verdict: "Buy on Cheap", "Hold/Wait for a drop", or "Sell".',
        backstory='You are the boss. You take the strict numbers from the Analyst, the real-world context from the Macro Expert, and the warnings from the Skeptic. You make the final call for the user\'s portfolio.',
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    # TASKS
    task_quant = Task(
        description=f'Fetch the pre-computed SQL metrics from BigQuery for {asset_or_fund} using the tool provided. Use this to determine if the asset is mathematically cheap, expensive, or experiencing a volume spike.',
        agent=graham_analyst,
        expected_output="A summary of the asset's quantitative health, moving averages, and margin of safety."
    )

    task_macro = Task(
        description=f'Search the live web for recent news about {asset_or_fund} and the current Pakistan State Bank interest rate. Explain how the macro environment impacts the quantitative thesis.',
        agent=macro_expert,
        expected_output="A contextual analysis incorporating live news and interest rates."
    )

    task_risk = Task(
        description=f'Review the quantitative and macro arguments for {asset_or_fund}. Write a scathing critique highlighting what could go wrong, value traps, or ignored macro risks.',
        agent=risk_skeptic,
        expected_output="A pessimistic risk assessment highlighting potential flaws in investing in this asset."
    )

    task_cio = Task(
        description='Review all previous tasks carefully. Provide your final 1-paragraph verdict starting exactly with one of these three options: "Buy on Cheap", "Hold/Wait for a drop", or "Sell". Justify the conclusion using a synthesis of the best arguments.',
        agent=cio,
        expected_output="A final, single-paragraph verdict summarizing the complete analysis."
    )

    # ORCHESTRATION: Link them sequentially
    financial_crew = Crew(
        agents=[graham_analyst, macro_expert, risk_skeptic, cio],
        tasks=[task_quant, task_macro, task_risk, task_cio],
        process=Process.sequential,
        manager_llm=llm, 
        memory=False, # <--- ENFORCES NO BACKGROUND OPENAI EMBEDDINGS
        verbose=True
    )

    print(f"\n--- KICKING OFF CREW FOR: {asset_or_fund} ---\n")
    result = financial_crew.kickoff()
    return result

if __name__ == "__main__":
    # Test execution for Meezan Bank
    final_verdict = create_and_run_crew("MEBL.KA")
    print("\n==================================")
    print("      FINAL MULTI-AGENT Output      ")
    print("==================================\n")
    print(final_verdict)
