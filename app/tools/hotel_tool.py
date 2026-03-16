import os
import re
from serpapi import GoogleSearch
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

@tool
def search_hotels(location: str, check_in_date: str, check_out_date: str) -> list:
    """
    Search for hotels and return structured data including source links.
    """
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return [{"error": "SERPAPI_API_KEY not found"}] 

    params = {
        "engine": "google_hotels",
        "q": location,
        "gl": "my",           
        "hl": "en",        
        "currency": "MYR",    
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "api_key": api_key
    } 

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        properties = results.get("properties", []) 
        
        hotel_list = []
        for hotel in properties[:3]: # Limit to top 3 for efficiency 
            # Data Cleaning for Price 
            raw_price = str(hotel.get("rate_per_night", {}).get("lowest", "0"))
            clean_num = re.sub(r'[^\d.]', '', raw_price)
            numeric_price = float(clean_num) if clean_num else 0.0

            # --- Secondary Request: Fetch Exact Address ---
            exact_address = "Address not provided"  # Default if Map API fails
            map_params = {
                "engine": "google_maps",
                "q": f"{hotel.get('name')}, {location}",
                "api_key": api_key,
                "hl": "en"
            }
            try:
                map_search = GoogleSearch(map_params)
                map_results = map_search.get_dict()
                # Extract real address from Google Maps results 
                if "place_results" in map_results:
                    exact_address = map_results["place_results"].get("address", exact_address)
                elif "local_results" in map_results and len(map_results["local_results"]) > 0:
                    exact_address = map_results["local_results"][0].get("address", exact_address)
            except Exception:
                pass 

            # --- Now properly append to the list  ---
            hotel_list.append({
                "name": hotel.get("name"), 
                "location": exact_address,  # 🚨 FIX: Use the actual variable, not the string! 
                "price": numeric_price, 
                "rating": hotel.get("overall_rating", 0.0), 
                "map_source": f"https://www.google.com/maps/search/?api=1&query={hotel.get('name')}".replace(" ", "+"),
                "hotel_source": hotel.get("link", "https://www.google.com/hotels")
            })
            
        return hotel_list
    except Exception as e:
        return [{"error": str(e)}] 
    
    # --- TOOL TESTING BLOCK ---
if __name__ == "__main__":
   
    test_result = search_hotels.invoke({
        "location": "Bangkok",
        "check_in_date": "2026-03-26",
        "check_out_date": "2026-03-28"
    })
    
   
    import json
    print(json.dumps(test_result, indent=2))