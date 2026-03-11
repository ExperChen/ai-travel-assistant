import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
import sys
from pathlib import Path

# Ensure tools are importable
TOOLS_DIR = Path(__file__).resolve().parents[2]
if str(TOOLS_DIR) not in sys.path:
    sys.path.append(str(TOOLS_DIR))

from app.tools.hotel_tool import search_hotels

load_dotenv()

def run_hotel_agent(user_query: str):
    # 1. Initialize the latest Gemini model
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GOOGLE_LLM_MODEL", "gemini-2.5-flash"),
        temperature=0.2 
    )

    # 2. Define tools
    tools = [search_hotels]

    # 3. Modern System Prompt
    system_message = SystemMessage(content="""You are a premium travel consultant. 
    Your task is to fetch hotel data using tools, then filter them strictly based on user requirements.
    Always provide: Hotel Name, Price, Rating, Address, and a compelling reason for recommendation.
    """)

    # 4. Construct the Next-Gen LangGraph Agent
    agent_executor = create_react_agent(llm, tools, prompt=system_message)

    # 5. Execute
    print(f"\n🚀 Planning for: {user_query}\n")
    
    result = agent_executor.invoke({"messages": [("user", user_query)]})
    raw_content = result["messages"][-1].content
    
    # Smart unpack: strip complex signature structures and extract pure text
    final_answer = ""
    if isinstance(raw_content, list):
        # If data is wrapped in a list
        first_item = raw_content[0]
        if isinstance(first_item, list):  # Handle nested lists
            final_answer = first_item[0].get("text", str(raw_content))
        elif isinstance(first_item, dict):
            final_answer = first_item.get("text", str(raw_content))
        else:
            final_answer = str(raw_content)
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