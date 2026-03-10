import os
from serpapi import GoogleSearch
from dotenv import load_dotenv

# Load environment variables from the .env file to read your API key
load_dotenv()

def search_hotels(location: str, check_in_date: str, check_out_date: str) -> list:
    """
    This is a hotel search tool. When the AI needs to query real hotels, accommodation prices, and ratings for a user, it will call this tool.
    
    Parameters:
        location (str): Destination, e.g., "Tokyo, Japan" or "Kuala Lumpur"
        check_in_date (str): Check-in date, format YYYY-MM-DD
        check_out_date (str): Check-out date, format YYYY-MM-DD
    """
    
    # 1. Get your SerpAPI key
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return [{"error": "❌ SERPAPI_API_KEY not found. Please check if your .env file is configured correctly!"}]

    print(f"🏨 Connecting to SerpAPI, searching the web for hotels in {location}...")

    # 2. Set search parameters
    params = {
        "engine": "google_hotels",
        "q": location,
        "gl": "my",           # Search region (Malaysia)
        "hl": "en",        # Language
        "currency": "MYR",    
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "api_key": api_key
    }

    try:
        # 3. Send request to Google
        search = GoogleSearch(params)
        results = search.get_dict()

        if "error" in results:
            return [{"error": f"API Error: {results['error']}"}]

        # 4. Extract hotel list (properties)
        properties = results.get("properties", [])
        if not properties:
            return [{"message": "No hotel information found in this area."}]

        # 5. Format data for the AI, picking only the core information (top 5 hotels)
        hotel_list = []
        for hotel in properties[:5]:
            rate = hotel.get("rate_per_night", {})
            price = rate.get("lowest", "Unknown price")
            
            hotel_list.append({
                "name": hotel.get("name", "Unknown name"),
                "price": f"{price}",
                "rating": hotel.get("overall_rating", "No rating"),
                "reviews": hotel.get("reviews", 0),
                "description": hotel.get("description", "No description available")
            })
            
        return hotel_list

    except Exception as e:
        return [{"error": f"An exception occurred during execution: {str(e)}"}]


# --- The section below is for your local testing. The AI won't run this when calling the tool ---
if __name__ == "__main__":
    import json
    # Let's simulate a search for hotels in Penang

    print("--- Starting local test ---")
    test_results = search_hotels("Penang", "2026-05-01", "2026-05-05")
    
    print(json.dumps(test_results, indent=2, ensure_ascii=False))