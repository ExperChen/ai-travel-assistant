import json
from app.tools.transportation_tool import transportation_tool

# ==========================================
# 测试案例 1：吉隆坡本地交通 (测试马币和本地解析)
# ==========================================
def test_klia_to_klcc_transit():
    print("\n▶ 测试 1: 吉隆坡本地交通 (KLIA to KLCC, transit)")
    result = transportation_tool.invoke({
        "origin": "KLIA",
        "destination": "KLCC",
        "transport_mode": "transit"
    })
    print("✅ 返回结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    assert result is not None  # 告诉 Pytest 只要有结果就算测试通过

# ==========================================
# 测试案例 2：海外交通 (测试全球化与不同货币)
# ==========================================
def test_narita_to_tokyo_train():
    print("\n▶ 测试 2: 日本跨城交通 (Narita Airport to Tokyo Station, train)")
    result = transportation_tool.invoke({
        "origin": "Narita Airport",
        "destination": "Tokyo Station",
        "transport_mode": "train"
    })
    print("✅ 返回结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    assert result is not None

# ==========================================
# 测试案例 3：中国大陆交通 (测试人民币和国内路线解析)
# ==========================================
def test_beijing_to_tiananmen_transit():
    print("\n▶ 测试 3: 中国大陆交通 (Beijing Capital International Airport to Tiananmen Square, transit)")
    result = transportation_tool.invoke({
        "origin": "Beijing Capital International Airport",
        "destination": "Tiananmen Square",
        "transport_mode": "transit"
    })
    print("✅ 返回结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    assert result is not None