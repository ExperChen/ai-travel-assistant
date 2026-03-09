"""
Transport Search Tool
交通方案搜索工具

功能：
- 根据出发地、目的地、旅游天数、预算，智能判断可用交通方式
- 国际路线只提供机票方案
- 国内路线提供机票 / 高铁 / 火车三种方案
- 使用 SerpAPI 搜索真实票价信息
- 返回结构化交通方案供 Agent 使用
"""

from __future__ import annotations

import os
import re
from typing import Any

from langchain.tools import tool

try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False


# ── 已知国家/地区列表，用于判断是否跨国 ──────────────────────────────
_COUNTRIES = [
    "malaysia", "malaysia", "中国", "china", "japan", "日本", "korea", "韩国",
    "thailand", "泰国", "singapore", "新加坡", "indonesia", "印尼",
    "vietnam", "越南", "philippines", "菲律宾", "australia", "澳大利亚",
    "usa", "united states", "美国", "uk", "united kingdom", "英国",
    "france", "法国", "germany", "德国", "india", "印度",
]

_MALAYSIA_CITIES = [
    "kuala lumpur", "kl", "penang", "槟城", "johor bahru", "新山",
    "kota kinabalu", "亚庇", "kuching", "古晋", "malacca", "马六甲",
    "ipoh", "怡保", "george town", "langkawi", "兰卡威",
]

_CHINA_CITIES = [
    "北京", "上海", "广州", "深圳", "成都", "重庆", "杭州", "西安",
    "南京", "武汉", "天津", "青岛", "厦门", "昆明", "三亚", "哈尔滨",
    "长沙", "郑州", "沈阳", "大连", "济南", "福州", "宁波", "苏州",
    "beijing", "shanghai", "guangzhou", "shenzhen", "chengdu",
    "hangzhou", "xian", "nanjing", "wuhan", "tianjin",
]


def _is_international(origin: str, destination: str) -> bool:
    """判断是否为跨国路线。"""
    origin_l = origin.lower()
    dest_l = destination.lower()

    origin_in_malaysia = any(c in origin_l for c in _MALAYSIA_CITIES)
    dest_in_malaysia = any(c in dest_l for c in _MALAYSIA_CITIES)
    origin_in_china = any(c in origin_l for c in _CHINA_CITIES)
    dest_in_china = any(c in dest_l for c in _CHINA_CITIES)

    # 同属马来西亚城市
    if origin_in_malaysia and dest_in_malaysia:
        return False
    # 同属中国城市
    if origin_in_china and dest_in_china:
        return False
    # 一方是马来西亚，一方是中国，视为国际
    if (origin_in_malaysia and dest_in_china) or (origin_in_china and dest_in_malaysia):
        return True
    # 含国家关键词，且两地不同国
    origin_countries = [c for c in _COUNTRIES if c in origin_l]
    dest_countries = [c for c in _COUNTRIES if c in dest_l]
    if origin_countries and dest_countries and set(origin_countries) != set(dest_countries):
        return True
    # 默认：无法判断时按国际处理（保守策略）
    return True


def _extract_price(text: str) -> str:
    """从文本中提取价格信息。"""
    pattern = re.compile(
        r"(?:RM|MYR|CNY|RMB|USD|US\$|\$|€|£|¥|SGD)\s?\d+(?:[,\.]\d{1,3})*"
        r"|\d+(?:[,\.]\d{1,3})*\s?(?:RM|MYR|CNY|RMB|USD|SGD)",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    return match.group(0).strip() if match else ""


def _search_serpapi(query: str, api_key: str) -> list[dict[str, str]]:
    """用 SerpAPI 搜索并返回简化结果列表。"""
    if not SERPAPI_AVAILABLE:
        return []
    try:
        params = {
            "engine": "google",
            "q": query,
            "hl": "en",
            "num": 5,
            "api_key": api_key,
        }
        data = GoogleSearch(params).get_dict()
        results = []
        for item in data.get("organic_results", [])[:5]:
            title = str(item.get("title", "")).strip()
            link = str(item.get("link", "")).strip()
            snippet = str(item.get("snippet", "")).strip()
            price = _extract_price(snippet) or _extract_price(title)
            results.append({
                "title": title,
                "link": link,
                "snippet": snippet,
                "price": price,
            })
        return results
    except Exception:
        return []


def _build_flight_plan(
    origin: str,
    destination: str,
    days: int,
    budget: float,
    api_key: str,
) -> dict[str, Any]:
    """搜索机票方案。"""
    query = f"cheap flights {origin} to {destination} economy ticket price"
    results = _search_serpapi(query, api_key)

    prices = [r["price"] for r in results if r["price"]]
    booking_links = [
        {"name": r["title"], "url": r["link"]}
        for r in results
        if r["link"]
    ][:3]

    return {
        "transport_type": "✈️ 机票 Flight",
        "origin": origin,
        "destination": destination,
        "estimated_price": prices[0] if prices else "请前往订票网站查询",
        "booking_platforms": booking_links or [
            {"name": "Google Flights", "url": f"https://www.google.com/travel/flights?q=flights+from+{origin}+to+{destination}"},
            {"name": "Skyscanner", "url": f"https://www.skyscanner.com/transport/flights/{origin}/{destination}/"},
            {"name": "AirAsia", "url": "https://www.airasia.com"},
        ],
        "notes": "建议提前 2-4 周购票以获得更低价格",
        "within_budget": True,
    }


def _build_train_plan(
    origin: str,
    destination: str,
    days: int,
    budget: float,
    api_key: str,
    is_highspeed: bool = False,
) -> dict[str, Any]:
    """搜索火车/高铁方案。"""
    train_type = "高铁 High-Speed Rail" if is_highspeed else "火车 Train"
    emoji = "🚄" if is_highspeed else "🚂"
    query = f"{'high speed rail' if is_highspeed else 'train'} {origin} to {destination} ticket price"
    results = _search_serpapi(query, api_key)

    prices = [r["price"] for r in results if r["price"]]
    booking_links = [
        {"name": r["title"], "url": r["link"]}
        for r in results
        if r["link"]
    ][:3]

    default_links = (
        [
            {"name": "12306 (中国高铁)", "url": "https://www.12306.cn"},
            {"name": "KTM Berhad (马来西亚火车)", "url": "https://www.ktmb.com.my"},
        ]
        if not booking_links
        else booking_links
    )

    return {
        "transport_type": f"{emoji} {train_type}",
        "origin": origin,
        "destination": destination,
        "estimated_price": prices[0] if prices else "请前往订票网站查询",
        "booking_platforms": default_links,
        "notes": "高铁/火车适合国内中短途，性价比高" if is_highspeed else "普通火车价格更低，适合预算有限的旅行者",
        "within_budget": True,
    }


def search_transport_options(
    origin: str,
    destination: str,
    days: int,
    budget: float,
) -> dict[str, Any]:
    """
    核心函数：搜索并返回交通方案。

    Args:
        origin: 出发地，例如 "Kuala Lumpur" 或 "北京"
        destination: 目的地，例如 "Tokyo" 或 "上海"
        days: 旅游天数
        budget: 总预算（单位与货币由用户输入决定）

    Returns:
        包含可用交通方案列表的字典
    """
    api_key = os.getenv("SERPAPI_API_KEY", "").strip()
    is_intl = _is_international(origin, destination)

    plans = []

    if is_intl:
        # 国际路线：只提供机票
        flight = _build_flight_plan(origin, destination, days, budget, api_key)
        plans.append(flight)
        route_type = "国际路线 International Route"
        note = "跨国路线仅提供机票方案"
    else:
        # 国内路线：提供机票 + 高铁 + 火车三种方案
        flight = _build_flight_plan(origin, destination, days, budget, api_key)
        highspeed = _build_train_plan(origin, destination, days, budget, api_key, is_highspeed=True)
        train = _build_train_plan(origin, destination, days, budget, api_key, is_highspeed=False)
        plans.extend([flight, highspeed, train])
        route_type = "国内路线 Domestic Route"
        note = "已为您提供机票、高铁、火车三种方案，请根据预算和时间选择"

    return {
        "origin": origin,
        "destination": destination,
        "days": days,
        "budget": budget,
        "route_type": route_type,
        "note": note,
        "transport_plans": plans,
        "tip": f"以上为单程票价参考，往返请乘以2。{days}天行程建议预留交通预算约占总预算的 20-30%。",
    }


@tool
def transport_search_tool(
    origin: str,
    destination: str,
    days: int,
    budget: float,
) -> dict[str, Any]:
    """
    交通方案搜索工具：根据出发地、目的地、天数和预算，智能搜索并推荐交通方案。

    - 国际路线（跨国）：只提供机票方案
    - 国内路线：提供机票、高铁、火车三种方案
    - 返回各平台订票链接和参考价格

    Args:
        origin: 出发城市，例如 "Kuala Lumpur", "北京", "Singapore"
        destination: 目的城市，例如 "Tokyo", "上海", "Penang"
        days: 旅游天数，例如 5
        budget: 总旅游预算，例如 3000.0
    """
    return search_transport_options(
        origin=origin,
        destination=destination,
        days=days,
        budget=budget,
    )