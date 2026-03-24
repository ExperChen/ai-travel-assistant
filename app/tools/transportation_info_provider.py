from typing import Any
from serpapi import GoogleSearch

# 统一配置加载
from app.config import Config

def fetch_transport_details(origin: str, destination: str, transport_mode: str = "all") -> dict[str, Any]:
    """
    纯净版交通抓取底层逻辑：
    - 移除所有价格抓取逻辑
    - 移除所有 Emoji
    - 返回全中文键值对的纯净字典
    """
    api_key = getattr(Config, "SERPAPI_API_KEY", "").strip()

    # 纯中文的返回结构
    result = {
        "出发地": origin,
        "目的地": destination,
        "路线方案": [] 
    }

    if not api_key:
        return result

    # 第一路：抓取【驾车/打车】方案
    try:
        drive_params = {
            "engine": "google_maps_directions",
            "start_addr": origin,
            "end_addr": destination,
            "travel_mode": 0,  # 0 = 驾车
            "hl": "zh-CN",     # 强制中文
            "api_key": api_key
        }
        drive_data = GoogleSearch(drive_params).get_dict()
        if "directions" in drive_data and len(drive_data["directions"]) > 0:
            route = drive_data["directions"][0]
            road_name = route.get("title", "常规路线")
            result["路线方案"].append({
                "方案类型": f"驾车 ({road_name})",
                "预估耗时": route.get("formatted_duration", "未知"),
                "行驶距离": route.get("formatted_distance", "未知")
            })
    except Exception:
        pass

    # 第二路：抓取【公共交通】方案
    try:
        transit_params = {
            "engine": "google_maps_directions",
            "start_addr": origin,
            "end_addr": destination,
            "travel_mode": 3,  # 3 = 公共交通
            "departure_time": "now", 
            "hl": "zh-CN",
            "api_key": api_key
        }
        transit_data = GoogleSearch(transit_params).get_dict()
        if "directions" in transit_data and len(transit_data["directions"]) > 0:
            route = transit_data["directions"][0]
            title = route.get("title", "")
            plan_name = f"公共交通 ({title})" if title else "最佳公共交通"
            
            result["路线方案"].append({
                "方案类型": plan_name,
                "预估耗时": route.get("formatted_duration", "未知"),
                "行驶距离": route.get("formatted_distance", "未知")
            })
    except Exception:
        pass

    return result