import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
from app.tools.hotel_tool import search_hotels
from datetime import datetime

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
    
    last_message = result["messages"][-1]
    
    if hasattr(last_message, "content"):
        raw_content = last_message.content
        
        if isinstance(raw_content, list):
            raw_content = raw_content[0].get("text", str(raw_content[0]))
    else:
        raw_content = str(last_message)

    clean_json = str(raw_content).replace("```json", "").replace("```", "").strip()
  
    try:
        
        if clean_json.startswith("content='") or clean_json.startswith('content="'):
           
            start = clean_json.find("[")
            end = clean_json.rfind("]") + 1
            if start != -1 and end != 0:
                clean_json = clean_json[start:end]

        parsed_data = json.loads(clean_json)
        print("\n" + "="*60)
        print("🏨 SUCCESS! PRETTY HOTEL RESULTS")
        print("="*60)
        print(json.dumps(parsed_data, indent=4, ensure_ascii=False))
        print("="*60)
    except Exception as e:
        print("\n⚠️ Formatting Warning: Printing raw content below")
        print(clean_json)

    return clean_json
   

if __name__ == "__main__":
    import json
    from datetime import datetime

    print("--- 🏨 AI Hotel Booking Assistant ---")
    
    while True:
        city = input("Enter destination city (e.g., Penang): ").strip()
        if city:
            break
        print("❌ City name cannot be empty. Please try again.")

   
    while True:
        check_in_str = input("Enter check-in date (YYYY-MM-DD): ")
        check_out_str = input("Enter check-out date (YYYY-MM-DD): ")

        def validate_dates(in_str, out_str):
            try:
                today = datetime.now().date()
                check_in_date = datetime.strptime(in_str, "%Y-%m-%d").date()
                check_out_date = datetime.strptime(out_str, "%Y-%m-%d").date()

                if check_in_date < today:
                    return False, "Check-in date must be today or later."
                if check_out_date <= check_in_date:
                    return False, "Check-out date must be after the check-in date."
                return True, None
            except ValueError:
                return False, "Invalid date format. Please use YYYY-MM-DD."

        is_valid, error_msg = validate_dates(check_in_str, check_out_str)
        
        if is_valid:
            break  
        else:
            print(f"❌ Error: {error_msg} Please re-enter both dates.")

    user_input_json = json.dumps({
        "city": city,
        "check_in": check_in_str,
        "check_out": check_out_str,
        "guests": 2,  
        "budget": { "min": 0, "max": 10000, "currency": "MYR" } 
    })

    print(f"\n🚀 Processing request for {city} from {check_in_str} to {check_out_str}...")
    run_hotel_agent(user_input_json)
    
    