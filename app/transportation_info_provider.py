import os
import re
from typing import Any
from serpapi import GoogleSearch

# 完美的货币正则解析器
_PRICE_REGEX = re.compile(
    r"(?:(?:RM|MYR|USD|SGD|EUR|GBP|AUD|CNY|RMB|JPY|THB|IDR|PHP|VND|INR|HKD|TWD|KRW)\s*\d+(?:,\d{3})*(?:\.\d{1,2})?"
    r"|(?:US\$|S\$|€|£|¥|\$)\s*\d+(?:,\d{3})*(?:\.\d{1,2})?"
    r"|\d+(?:,\d{3})*(?:\.\d{1,2})?\s*(?:RM|MYR|USD|SGD|EUR|GBP|AUD|CNY|RMB|JPY|THB|IDR|PHP|VND|INR|HKD|TWD|KRW))",
    re.IGNORECASE,
)

def _get_overall_price(origin: str, dest: str, api_key: str) -> str:
    """引擎 B：抓取宏观交通票价 (Rome2Rio 纯净版)"""
    try:
        query = f"{origin} to {dest} transit train bus fare price site:rome2rio.com"
        params = {"engine": "google", "q": query, "hl": "en", "num": 3, "api_key": api_key}
        data = GoogleSearch(params).get_dict()
        
        text_pool = []
        for item in data.get("organic_results", []):
            text_pool.append(str(item.get("snippet", "")))
            
        merged_text = " ".join(text_pool)
        prices = _PRICE_REGEX.findall(merged_text)
        
        if prices:
            unique_prices = []
            for p in prices:
                p_clean = p.strip()
                if p_clean not in unique_prices:
                    unique_prices.append(p_clean)
            
            # 识别主货币，过滤杂项
            main_currency = re.sub(r'[\d\,\.\s]', '', unique_prices[0])
            filtered_prices = [p for p in unique_prices if main_currency in p]
            
            # 真实的数字大小排序
            def extract_num(s):
                nums = re.findall(r'\d+(?:,\d{3})*(?:\.\d{1,2})?', s)
                return float(nums[0].replace(',', '')) if nums else 0.0
                
            filtered_prices.sort(key=extract_num)
            return " - ".join(filtered_prices[:2])
            
        return "未能抓取到确切数字"
    except Exception:
        return "获取价格失败"

def fetch_transport_details(origin: str, destination: str, transport_mode: str = "all") -> dict[str, Any]:
    """
    终极架构：并发获取【最优驾车】+【最优公交】
    """
    api_key = os.getenv("SERPAPI_API_KEY", "").strip()

    result = {
        "origin": origin,
        "destination": destination,
        "overall_estimated_price": "未知",
        "routes": [] 
    }

    if not api_key:
        return result

    # 第一路：抓取【最优驾车/打车】方案
    try:
        drive_params = {
            "engine": "google_maps_directions",
            "start_addr": origin,
            "end_addr": destination,
            "travel_mode": 0,  # 0 = 驾车
            "hl": "zh-CN",
            "api_key": api_key
        }
        drive_data = GoogleSearch(drive_params).get_dict()
        if "directions" in drive_data and len(drive_data["directions"]) > 0:
            route = drive_data["directions"][0]
            road_name = route.get("title", "常规路线")
            result["routes"].append({
                "plan_name": f"🚗 驾车/打车 ({road_name})",
                "total_duration": route.get("formatted_duration", "未知"),
                "distance": route.get("formatted_distance", "未知")
            })
    except Exception as e:
        print(f"驾车路线抓取异常: {e}")

    # 第二路：抓取【最优公共交通】方案
    try:
        transit_params = {
            "engine": "google_maps_directions",
            "start_addr": origin,
            "end_addr": destination,
            "travel_mode": 3,  # 3 = 公共交通
            "departure_time": "now", # 强制唤醒公交时刻表
            "hl": "zh-CN",
            "api_key": api_key
        }
        transit_data = GoogleSearch(transit_params).get_dict()
        if "directions" in transit_data and len(transit_data["directions"]) > 0:
            route = transit_data["directions"][0]
            title = route.get("title", "")
            plan_name = f"🚆 公共交通 ({title})" if title else "🚆 最佳公共交通"
            
            result["routes"].append({
                "plan_name": plan_name,
                "total_duration": route.get("formatted_duration", "未知"),
                "distance": route.get("formatted_distance", "未知")
            })
    except Exception as e:
        print(f"公交路线抓取异常: {e}")

    result["overall_estimated_price"] = _get_overall_price(origin, destination, api_key)

    return result