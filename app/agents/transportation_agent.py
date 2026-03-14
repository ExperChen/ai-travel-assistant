import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# 导入你刚刚拆分出去的新工具
from app.tools.multi_route_tool import optimize_multi_location_route

load_dotenv()

# ==========================================
# 终极架构：绕过 Agent 模块，直接底层 Tool Calling
# ==========================================
def run_travel_agent(user_query: str):
    """自然语言对话入口"""
    # 1. 初始化大模型
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # 2. 将工具直接“绑”在模型上（绕过所有复杂的 Agent 组装器）
    llm_with_tools = llm.bind_tools([optimize_multi_location_route])
    
    print(f"🌍 大模型正在分析你的自然语言: {user_query}")
    
    # 3. 让大模型直接处理自然语言，它会自动决定是否调用工具以及提取参数
    ai_msg = llm_with_tools.invoke(user_query)
    
    # 4. 拦截并处理工具调用
    if ai_msg.tool_calls:
        print("⏳ 成功提取到地点，正在底层算力引擎中穷举最优路径...\n")
        
        # 提取大模型从你的话里抓出来的参数 (比如 ["王府井", "天安门", "颐和园"])
        tool_call = ai_msg.tool_calls[0]
        locations_arg = tool_call["args"]["locations"]
        
        # 5. 直接运行我们的纯 Python 工具函数！
        # optimize_multi_location_route.invoke 是调用 @tool 装饰器的标准方法
        result_json = optimize_multi_location_route.invoke({"locations": locations_arg})
        
        # 直接把工具算出来的纯净中文 JSON 返回，不给大模型任何废话的机会
        return result_json
    else:
        return '{"错误": "未能识别出需要规划的地点，请换个说法试试。"}'

# ==========================================
# 测试运行
# ==========================================
if __name__ == "__main__":
    test_query = "我明天在北京，想去 王府井、天安门、颐和园 这三个地方，帮我算一下怎么走路上花的时间最少？返回json给我。"
    
    result = run_travel_agent(test_query)
    
    print("🎯 最终纯净 JSON 输出：")
    print(result)