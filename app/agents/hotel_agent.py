import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
from app.tools.hotel_tool import search_hotels

load_dotenv()

def run_hotel_agent(json_input: str):
    # Parse lead's JSON input
    data = json.loads(json_input)
    city = data.get("city")
    check_in = data.get("check_in")
    check_out = data.get("check_out")

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

    # Strict system instruction based on documentation requirements 
    system_prompt = SystemMessage(content="""You are a Data API. 
    Return hotel results strictly in JSON format with fields: name, location, arrive_date, leave_date, price, rating, map_source, hotel_source.
    - price must be a float.
    - NO markdown like ```json.
    """)

    agent = create_react_agent(llm, [search_hotels], prompt=system_prompt)
    
    # Internal trigger to fetch data 
    query = f"Search hotels in {city} from {check_in} to {check_out} and return pure JSON."
    result = agent.invoke({"messages": [("user", query)]})
    
    # Clean output for a beautiful JSON look
    raw_content = result["messages"][-1].content
    clean_json = raw_content.replace("```json", "").replace("```", "").strip()
    
    print(clean_json)
    return clean_json

if __name__ == "__main__":
    lead_input = """
    {
      "city": "Bangkok",
      "check_in": "2026-03-26",
      "check_out": "2026-03-28",
      "guests": 2,
      "budget": { "min": 1000, "max": 5000, "currency": "CNY" }
    }
    """
    run_hotel_agent(lead_input)