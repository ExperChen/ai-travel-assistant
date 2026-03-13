import json
import os
from dotenv import load_dotenv  

# 自动加载环境变量，妈妈再也不用担心我弄丢秘钥了！
load_dotenv()

from app.transportation_tool import transportation_tool

def run_tests():
    # 提醒：确保你的 .env 文件里配置了 SERPAPI_API_KEY
    if not os.getenv("SERPAPI_API_KEY"):
        print("⚠️ 警告：环境变量中未找到 SERPAPI_API_KEY。")
        print("请确保你已经在本地配置了包含 API Key 的 .env 文件！\n")
        return  

    print("开始测试 transportation_tool...\n")

    # ==========================================
    # 测试案例 1：吉隆坡本地交通 (测试马币和本地解析)
    # ==========================================
    print("▶ 测试 1: 吉隆坡本地交通 (KLIA to KLCC, transit)")
    try:
        result1 = transportation_tool.invoke({
            "origin": "KLIA",
            "destination": "KLCC",
            "transport_mode": "transit"
        })
        print("✅ 测试 1 成功！返回结果:")
        print(json.dumps(result1, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ 测试 1 失败: {e}")

    print("\n" + "="*50 + "\n")

    # ==========================================
    # 测试案例 2：海外交通 (测试全球化与不同货币)
    # ==========================================
    print("▶ 测试 2: 日本跨城交通 (Narita Airport to Tokyo Station, train)")
    try:
        result2 = transportation_tool.invoke({
            "origin": "Narita Airport",
            "destination": "Tokyo Station",
            "transport_mode": "train"
        })
        print("✅ 测试 2 成功！返回结果:")
        print(json.dumps(result2, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ 测试 2 失败: {e}")

    print("\n" + "="*50 + "\n")

    # ==========================================
    # 测试案例 3：中国大陆交通 (测试人民币和国内路线解析)
    # ==========================================
    print("▶ 测试 3: 中国大陆交通 (Beijing Capital International Airport to Tiananmen Square, transit)")
    try:
        result3 = transportation_tool.invoke({
            "origin": "Beijing Capital International Airport",
            "destination": "Tiananmen Square",
            "transport_mode": "transit"
        })
        print("✅ 测试 3 成功！返回结果:")
        print(json.dumps(result3, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ 测试 3 失败: {e}")

if __name__ == "__main__":
    run_tests()