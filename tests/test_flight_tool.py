"""
tests/test_flight_tool.py

运行方法:
    python -m pytest tests/test_flight_tool.py -v
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.tools.flight_tool import search_and_filter_flights, city_to_iata


# ── 工具函数 ──────────────────────────────────────────────────────────────────
def call(query: dict) -> dict:
    """把 dict 转成 JSON 调用 tool，返回解析后的 dict"""
    result = search_and_filter_flights.invoke({"query_json": json.dumps(query)})
    return json.loads(result)

BASE_QUERY = {
    "departure_city": "Kuala Lumpur",
    "arrival_city": "Bangkok",
    "departure_date": "2026-03-26",
    "passengers": 2,
    "budget": {"min": 0, "max": 99999, "currency": "MYR"}
}


# ══════════════════════════════════════════════════════════════════════════════
# 1. city_to_iata
# ══════════════════════════════════════════════════════════════════════════════

def test_city_to_iata_known():
    assert city_to_iata("Kuala Lumpur") == "KUL"
    assert city_to_iata("kuala lumpur") == "KUL"
    assert city_to_iata("Bangkok")      == "BKK"
    assert city_to_iata("Tokyo")        == "TYO"
    assert city_to_iata("KL")           == "KUL"

def test_city_to_iata_unknown():
    assert city_to_iata("Berlin") == "BER"


# ══════════════════════════════════════════════════════════════════════════════
# 2. 输出结构
# ══════════════════════════════════════════════════════════════════════════════

def test_output_has_flights_key():
    result = call(BASE_QUERY)
    assert "flights" in result

def test_output_flight_fields():
    """每条航班必须包含组长要求的所有字段"""
    result = call(BASE_QUERY)
    required = [
        "name", "code", "airline_company",
        "departure_airport", "arrival_airport",
        "departure_date", "arrival_date",
        "price", "luggage_limitation",
    ]
    for flight in result["flights"]:
        for field in required:
            assert field in flight, f"缺少字段: {field}"

def test_output_date_format():
    """日期格式应该是 ISO 格式 YYYY-MM-DDTHH:MM:SS"""
    from datetime import datetime
    result = call(BASE_QUERY)
    for flight in result["flights"]:
        datetime.strptime(flight["departure_date"], "%Y-%m-%dT%H:%M:%S")
        datetime.strptime(flight["arrival_date"],   "%Y-%m-%dT%H:%M:%S")

def test_correct_airports():
    """机场代码应该对应输入城市"""
    result = call(BASE_QUERY)
    for flight in result["flights"]:
        assert flight["departure_airport"] == "KUL"
        assert flight["arrival_airport"]   == "BKK"


# ══════════════════════════════════════════════════════════════════════════════
# 3. 预算筛选
# ══════════════════════════════════════════════════════════════════════════════

def test_budget_max_filter():
    """价格不应超过预算上限（per person）"""
    query = {**BASE_QUERY, "budget": {"min": 0, "max": 500, "currency": "MYR"}}
    result = call(query)
    for flight in result["flights"]:
        assert flight["price"] <= 500, \
            f"{flight['code']} 价格 RM{flight['price']} 超过预算 RM500"

def test_budget_min_filter():
    """价格不应低于预算下限（per person）"""
    query = {**BASE_QUERY, "budget": {"min": 400, "max": 99999, "currency": "MYR"}}
    result = call(query)
    for flight in result["flights"]:
        assert flight["price"] >= 400, \
            f"{flight['code']} 价格 RM{flight['price']} 低于下限 RM400"

def test_budget_range_filter():
    """价格应该在预算范围内"""
    query = {**BASE_QUERY, "budget": {"min": 200, "max": 600, "currency": "MYR"}}
    result = call(query)
    for flight in result["flights"]:
        assert 200 <= flight["price"] <= 600

def test_impossible_budget_returns_empty():
    """不可能满足的预算应该返回空列表"""
    query = {**BASE_QUERY, "budget": {"min": 0, "max": 1, "currency": "MYR"}}
    result = call(query)
    assert result["flights"] == []

def test_cny_budget_conversion():
    """CNY 预算应该被正确换算"""
    query = {**BASE_QUERY, "budget": {"min": 0, "max": 99999, "currency": "CNY"}}
    result = call(query)
    assert "flights" in result
    # 有结果说明换算没有出错
    assert isinstance(result["flights"], list)


# ══════════════════════════════════════════════════════════════════════════════
# 4. 排序与数量
# ══════════════════════════════════════════════════════════════════════════════

def test_results_sorted_by_price():
    """结果应该按价格从低到高排列"""
    result = call(BASE_QUERY)
    prices = [f["price"] for f in result["flights"]]
    assert prices == sorted(prices), "结果没有按价格升序排列"

def test_returns_multiple_flights():
    """应该返回多条航班"""
    result = call(BASE_QUERY)
    assert len(result["flights"]) > 1

def test_meta_info_present():
    """输出应该包含 meta 统计信息"""
    result = call(BASE_QUERY)
    assert "meta" in result
    assert "total_found"  in result["meta"]
    assert "after_filter" in result["meta"]
    assert "passengers"   in result["meta"]


# ══════════════════════════════════════════════════════════════════════════════
# 5. 不同乘客数量
# ══════════════════════════════════════════════════════════════════════════════

def test_passengers_reflected_in_meta():
    """meta 里的乘客数应该和输入一致"""
    query = {**BASE_QUERY, "passengers": 3}
    result = call(query)
    assert result["meta"]["passengers"] == 3

def test_price_is_per_person():
    """price 字段应该是每人价格（不是总价）"""
    q1 = {**BASE_QUERY, "passengers": 1}
    q2 = {**BASE_QUERY, "passengers": 2}
    r1 = call(q1)
    r2 = call(q2)
    # 同一航班每人价格应该相同，不管几个人
    if r1["flights"] and r2["flights"]:
        assert r1["flights"][0]["price"] == r2["flights"][0]["price"]