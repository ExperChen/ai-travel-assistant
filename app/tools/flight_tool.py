"""
flight_tool.py - 机票查询工具

输入格式:
{
  "departure_city": "Kuala Lumpur",
  "arrival_city": "Bangkok",
  "departure_date": "2026-03-26",
  "passengers": 2,
  "budget": {
    "min": 1000,
    "max": 5000,
    "currency": "MYR"
  }
}

输出格式:
{
  "flights": [
    {
      "name": "Malaysia Airlines",
      "code": "MH782",
      "airline_company": "MAS",
      "departure_airport": "KUL",
      "arrival_airport": "BKK",
      "departure_date": "2026-03-26T14:00:00",
      "arrival_date": "2026-03-26T15:10:00",
      "price": 450.00,
      "luggage_limitation": "20kg"
    }
  ]
}
"""

import os
import json
import random
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

# ── Amadeus API（可选，没有就用模拟数据）─────────────────────────────────────
USE_REAL_API = False
try:
    from amadeus import Client as AmadeusClient, ResponseError
    _cid = os.getenv("AMADEUS_CLIENT_ID")
    _sec = os.getenv("AMADEUS_CLIENT_SECRET")
    if _cid and _sec:
        amadeus = AmadeusClient(client_id=_cid, client_secret=_sec)
        USE_REAL_API = True
except Exception:
    pass

# ── 城市名 → IATA 代码 ────────────────────────────────────────────────────────
CITY_TO_IATA = {
    "kuala lumpur": "KUL", "kl": "KUL",
    "tokyo": "TYO", "osaka": "KIX",
    "singapore": "SIN", "bangkok": "BKK",
    "london": "LHR", "paris": "CDG",
    "new york": "JFK", "sydney": "SYD",
    "seoul": "ICN", "beijing": "PEK",
    "shanghai": "PVG", "hong kong": "HKG",
    "dubai": "DXB", "amsterdam": "AMS",
    "frankfurt": "FRA", "taipei": "TPE",
    "jakarta": "CGK", "manila": "MNL",
}

def city_to_iata(city: str) -> str:
    return CITY_TO_IATA.get(city.lower().strip(), city.upper()[:3])

# ── 航司代码 → 全名/简称 ──────────────────────────────────────────────────────
AIRLINE_INFO = {
    "AK": {"name": "AirAsia",             "company": "AirAsia"},
    "MH": {"name": "Malaysia Airlines",   "company": "MAS"},
    "JL": {"name": "Japan Airlines",      "company": "JAL"},
    "NH": {"name": "ANA",                 "company": "ANA"},
    "TR": {"name": "Scoot",               "company": "Scoot"},
    "D7": {"name": "AirAsia X",           "company": "AirAsia X"},
    "OD": {"name": "Batik Air",           "company": "Batik Air"},
    "PR": {"name": "Philippine Airlines", "company": "PAL"},
    "SQ": {"name": "Singapore Airlines",  "company": "SIA"},
    "TG": {"name": "Thai Airways",        "company": "THAI"},
}

# ── 货币换算（简单固定汇率，仅供演示）────────────────────────────────────────
EXCHANGE_TO_MYR = {
    "MYR": 1.0,
    "CNY": 0.94,   # 1 CNY ≈ 0.94 MYR (示例)
    "USD": 4.70,
    "SGD": 3.50,
}

def convert_to_myr(amount: float, currency: str) -> float:
    rate = EXCHANGE_TO_MYR.get(currency.upper(), 1.0)
    return amount * rate


# ══════════════════════════════════════════════════════════════════════════════
# 模拟数据生成
# ══════════════════════════════════════════════════════════════════════════════
def _generate_mock_flights(origin: str, destination: str,
                           departure_date: str, passengers: int) -> list[dict]:
    airlines = [
        ("AK", False, True,  "20kg", 150, 600),
        ("MH", True,  True,  "20kg", 400, 900),
        ("D7", False, True,  "20kg", 200, 700),
        ("TR", False, False, None,   180, 650),
        ("OD", False, True,  "20kg", 170, 580),
        ("SQ", True,  True,  "30kg", 600, 1200),
        ("TG", True,  True,  "20kg", 500, 1000),
        ("PR", True,  True,  "20kg", 350, 850),
    ]
    random.seed(hash(departure_date + origin + destination) % 10000)
    flights = []

    for code, is_direct, has_bag, bag_kg, min_p, max_p in airlines:
        for _ in range(3):
            dep_h = random.randint(6, 22)
            dep_m = random.choice([0, 15, 30, 45])
            fly_h = random.randint(1, 3) if is_direct else random.randint(5, 10)
            fly_m = random.choice([0, 15, 30, 45])

            dep_dt = datetime.strptime(departure_date, "%Y-%m-%d").replace(
                hour=dep_h, minute=dep_m)
            arr_dt = dep_dt + timedelta(hours=fly_h, minutes=fly_m)

            price_per_pax = round(random.uniform(min_p, max_p), 2)
            info = AIRLINE_INFO.get(code, {"name": code, "company": code})
            flight_num = f"{code}{random.randint(100, 999)}"

            flights.append({
                "name":              info["name"],
                "code":              flight_num,
                "airline_company":   info["company"],
                "departure_airport": origin,
                "arrival_airport":   destination,
                "departure_date":    dep_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "arrival_date":      arr_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "price":             price_per_pax,
                "total_price":       round(price_per_pax * passengers, 2),
                "luggage_limitation": bag_kg if has_bag else "No checked bag",
                "is_direct":         is_direct,
                "passengers":        passengers,
            })

    return flights


# ══════════════════════════════════════════════════════════════════════════════
# 核心工具函数（供 Agent 调用）
# ══════════════════════════════════════════════════════════════════════════════

@tool
def search_and_filter_flights(query_json: str) -> str:
    """
    根据输入的 JSON 查询并筛选机票，返回符合条件的航班列表。

    输入 JSON 格式:
    {
      "departure_city": "Kuala Lumpur",
      "arrival_city": "Bangkok",
      "departure_date": "2026-03-26",
      "passengers": 2,
      "budget": {
        "min": 1000,
        "max": 5000,
        "currency": "MYR"
      }
    }

    输出 JSON 格式:
    {
      "flights": [
        {
          "name": "Malaysia Airlines",
          "code": "MH782",
          "airline_company": "MAS",
          "departure_airport": "KUL",
          "arrival_airport": "BKK",
          "departure_date": "2026-03-26T14:00:00",
          "arrival_date": "2026-03-26T15:10:00",
          "price": 450.00,
          "luggage_limitation": "20kg"
        }
      ]
    }
    """
    # ── 解析输入 ──────────────────────────────────────────────────────────────
    try:
        query = json.loads(query_json)
    except Exception as e:
        return json.dumps({"error": f"输入 JSON 解析失败: {e}"}, ensure_ascii=False)

    departure_city = query.get("departure_city", "")
    arrival_city   = query.get("arrival_city", "")
    departure_date = query.get("departure_date", "")
    passengers     = query.get("passengers", 1)
    budget         = query.get("budget", {})
    budget_min     = budget.get("min", 0)
    budget_max     = budget.get("max", 99999)
    currency       = budget.get("currency", "MYR")

    # 预算转换为 MYR（per person）
    budget_min_myr = convert_to_myr(budget_min, currency) / passengers
    budget_max_myr = convert_to_myr(budget_max, currency) / passengers

    origin = city_to_iata(departure_city)
    dest   = city_to_iata(arrival_city)

    # ── 搜索航班 ──────────────────────────────────────────────────────────────
    if USE_REAL_API:
        try:
            response = amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=dest,
                departureDate=departure_date,
                adults=passengers,
                currencyCode="MYR",
                max=30,
            )
            raw_flights = []
            for offer in response.data:
                itin  = offer["itineraries"][0]
                segs  = itin["segments"]
                first = segs[0]
                last  = segs[-1]
                price = offer["price"]
                tp    = offer.get("travelerPricings", [{}])[0]
                fd    = tp.get("fareDetailsBySegment", [{}])[0]
                bags  = fd.get("includedCheckedBags", {})
                total = float(price.get("grandTotal", 0))
                code  = first["carrierCode"]
                info  = AIRLINE_INFO.get(code, {"name": code, "company": code})

                raw_flights.append({
                    "name":              info["name"],
                    "code":              f"{code}{first['number']}",
                    "airline_company":   info["company"],
                    "departure_airport": first["departure"]["iataCode"],
                    "arrival_airport":   last["arrival"]["iataCode"],
                    "departure_date":    first["departure"]["at"][:19],
                    "arrival_date":      last["arrival"]["at"][:19],
                    "price":             round(total / passengers, 2),
                    "total_price":       total,
                    "luggage_limitation": f"{bags.get('weight',0)}kg" if bags.get("quantity",0) > 0 else "No checked bag",
                    "is_direct":         len(segs) == 1,
                    "passengers":        passengers,
                })
        except Exception as e:
            return json.dumps({"error": f"Amadeus API 错误: {e}"}, ensure_ascii=False)
    else:
        raw_flights = _generate_mock_flights(origin, dest, departure_date, passengers)

    # ── 筛选：预算范围 ────────────────────────────────────────────────────────
    filtered = [
        f for f in raw_flights
        if budget_min_myr <= f["price"] <= budget_max_myr
    ]

    # ── 按价格升序排列 ────────────────────────────────────────────────────────
    filtered.sort(key=lambda x: x["price"])

    # ── 只保留输出所需字段 ────────────────────────────────────────────────────
    output_flights = []
    for f in filtered:
        output_flights.append({
            "name":              f["name"],
            "code":              f["code"],
            "airline_company":   f["airline_company"],
            "departure_airport": f["departure_airport"],
            "arrival_airport":   f["arrival_airport"],
            "departure_date":    f["departure_date"],
            "arrival_date":      f["arrival_date"],
            "price":             f["price"],
            "luggage_limitation": f["luggage_limitation"],
        })

    return json.dumps({
        "flights": output_flights,
        "meta": {
            "total_found":    len(raw_flights),
            "after_filter":   len(output_flights),
            "currency":       "MYR",
            "passengers":     passengers,
            "budget_per_pax": f"{budget_min_myr:.0f} - {budget_max_myr:.0f} MYR",
        }
    }, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
# 直接运行测试
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    test_input = {
        "departure_city": "Kuala Lumpur",
        "arrival_city": "Bangkok",
        "departure_date": "2026-03-26",
        "passengers": 2,
        "budget": {
            "min": 1000,
            "max": 5000,
            "currency": "MYR"
        }
    }

    print("输入:")
    print(json.dumps(test_input, ensure_ascii=False, indent=2))
    print("\n输出:")
    result = search_and_filter_flights.invoke({"query_json": json.dumps(test_input)})
    print(result)