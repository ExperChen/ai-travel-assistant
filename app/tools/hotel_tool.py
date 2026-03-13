import os
import re
from urllib.parse import quote_plus
from serpapi import GoogleSearch
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()


def _pick_hotel_image_url(hotel: dict) -> str:
    for key in ("thumbnail", "image", "image_url"):
        value = str(hotel.get(key, "")).strip()
        if value.startswith("http"):
            return value

    images = hotel.get("images") or hotel.get("photos") or []
    if isinstance(images, list):
        for item in images:
            if isinstance(item, str):
                value = item.strip()
                if value.startswith("http"):
                    return value
            if isinstance(item, dict):
                for key in ("original", "thumbnail", "original_image", "image"):
                    value = str(item.get(key, "")).strip()
                    if value.startswith("http"):
                        return value

    return ""


@tool
def search_hotels(location: str, check_in_date: str, check_out_date: str) -> list:
    """
    Search for real hotels and fetch exact addresses using Google Maps.
    """
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return [{"error": "SERPAPI_API_KEY not found"}]

    print(f"🏨 [Step 1] Fetching hotel list for {location}...")

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
        if not properties:
            return [{"message": "No hotels found."}]

        hotel_list = []
        
        top_hotels = properties[:10]
        
        print(f"🔍 [Step 2] Fetching exact addresses for the top {len(top_hotels)} hotels...")

        for hotel in top_hotels:
            rate = hotel.get("rate_per_night", {})
            raw_price = str(rate.get("lowest", "Unknown"))
            
            if raw_price == "Unknown":
                continue
                
            hotel_name = hotel.get("name", "Unknown")
            print(f"   📍 Pinpointing address for: {hotel_name}")

            # 🧹 [Data Cleaning] Remove \xa0, letters, commas, etc., leaving only pure numbers
            clean_num_str = re.sub(r'[^\d.]', '', raw_price)
            numeric_price = float(clean_num_str) if clean_num_str else 9999
            final_price = f"RM {clean_num_str}" if clean_num_str else "Unknown"

            # --- Secondary Request: Fetch Exact Address ---
            exact_address = "Address not provided"
            map_params = {
                "engine": "google_maps",
                "q": f"{hotel_name}, {location}",
                "api_key": api_key,
                "hl": "en"
            }
            map_source_url = f"https://www.google.com/maps/search/{quote_plus(f'{hotel_name}, {location}')}"
            try:
                map_search = GoogleSearch(map_params)
                map_results = map_search.get_dict()
                
                if "place_results" in map_results:
                    exact_address = map_results["place_results"].get("address", exact_address)
                    map_source_url = map_results["place_results"].get("google_maps_url", map_source_url)
                elif "local_results" in map_results and len(map_results["local_results"]) > 0:
                    exact_address = map_results["local_results"][0].get("address", exact_address)
                    map_source_url = map_results.get("search_metadata", {}).get("google_maps_url", map_source_url)
            except Exception as e:
                pass 
            # ----------------------------------------------

            hotel_source_url = hotel.get("link", "")
            image_url = _pick_hotel_image_url(hotel)

            hotel_list.append({
                "name": hotel_name,
                "price": final_price,
                "numeric_price": numeric_price,
                "rating": hotel.get("overall_rating", 0),
                "reviews": hotel.get("reviews", 0),
                "address": exact_address,
                "hotel_source_url": hotel_source_url,
                "map_source_url": map_source_url,
                "image_url": image_url,
            })
            
        print(f"✅ Successfully processed {len(hotel_list)} hotels with real addresses!")
        return hotel_list

    except Exception as e:
        return [{"error": f"Exception: {str(e)}"}]

# --- TOOL TESTING BLOCK ---
if __name__ == "__main__":
    print("🔍 Testing Hotel Tool (with Address Fetching)...")
    test_result = search_hotels.invoke({
        "location": "Penang",
        "check_in_date": "2026-05-01",
        "check_out_date": "2026-05-05"
    })
    
    # 💄 Beautifully Formatted Output
    print("\n" + "=" * 60)
    print("✅ Test Complete! Clean and beautiful data below:")
    print("=" * 60)
    for i, hotel in enumerate(test_result):
        print(f"🏨 Hotel {i+1} : {hotel.get('name')}")
        print(f"💰 Price   : {hotel.get('price')} (Machine read value: {hotel.get('numeric_price')})")
        print(f"⭐ Rating  : {hotel.get('rating')} ({hotel.get('reviews')} reviews)")
        print(f"📍 Address : {hotel.get('address')}")
        print("-" * 60)
    print("\n")
