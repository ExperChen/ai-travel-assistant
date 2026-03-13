import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
import sys
from pathlib import Path

# Ensure tools are importable
TOOLS_DIR = Path(__file__).resolve().parents[2]
if str(TOOLS_DIR) not in sys.path:
    sys.path.append(str(TOOLS_DIR))

from app.tools.hotel_tool import search_hotels

load_dotenv()

def _is_quota_exhausted_error(exc: Exception) -> bool:
    text = str(exc)
    return (
        "RESOURCE_EXHAUSTED" in text
        or "Quota exceeded" in text
        or "You exceeded your current quota" in text
        or "generate_content_free_tier_requests" in text
    )

def _build_llm(use_google: bool):
    if use_google and os.getenv("GOOGLE_API_KEY"):
        return ChatGoogleGenerativeAI(
            model=os.getenv("GOOGLE_LLM_MODEL", "gemini-2.5-flash"),
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.2,
        )
    return ChatOpenAI(
        model=os.getenv("COMPANY_LLM_MODEL", "gpt-4o-mini"),
        base_url=os.getenv("COMPANY_BASE_URL"),
        api_key=os.getenv("COMPANY_API_KEY"),
        temperature=0.2,
    )

def run_hotel_agent(user_query: str):
    use_google = bool(os.getenv("GOOGLE_API_KEY"))
    llm = _build_llm(use_google)

    # 2. Define tools
    tools = [search_hotels]

    # 3. Modern System Prompt
    system_prompt = """You are a premium travel consultant. 
    Your task is to fetch hotel data using tools, then filter them strictly based on user requirements.
    Always provide: Hotel Name, Price, Rating, Address, and a compelling reason for recommendation.
    """

    # 4. Construct the latest LangChain Agent (built on LangGraph runtime)
    agent_executor = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
    )

    # 5. Execute
    print(f"\n🚀 Planning for: {user_query}\n")
    
    try:
        result = agent_executor.invoke({"messages": [{"role": "user", "content": user_query}]})
    except Exception as e:
        if use_google and _is_quota_exhausted_error(e):
            llm = _build_llm(False)
            agent_executor = create_agent(
                model=llm,
                tools=tools,
                system_prompt=system_prompt,
            )
            result = agent_executor.invoke({"messages": [{"role": "user", "content": user_query}]})
        else:
            raise
    raw_content = result["messages"][-1].content
    
    # Smart unpack: strip complex signature structures and extract pure text
    final_answer = ""
    if isinstance(raw_content, list):
        content_parts = []
        for item in raw_content:
            if isinstance(item, dict):
                content_parts.append(item.get("text", ""))
            else:
                content_parts.append(str(item))
        final_answer = "".join(content_parts) if content_parts else str(raw_content)
    else:
        # If it's already a string
        final_answer = str(raw_content)
        
    # Replace literal '\n' strings with actual newlines
    final_answer = final_answer.replace('\\n', '\n')
    
    print("\n" + "="*50)
    print("✅ Final Beautifully Formatted Report:")
    print("="*50)
    print(final_answer)
    print("="*50 + "\n")

if __name__ == "__main__":
    query = "Help me find 3 high-rated hotels in Penang for 2026-05-01 to 2026-05-05,  under RM 300 per night. Show addresses."
    run_hotel_agent(query)
