import os
from langchain_community.chat_models import ChatZhipuAI
from dotenv import load_dotenv

# 导入你的多地点路径规划工具
from app.tools.multi_route_tool import optimize_multi_location_route

# ==========================================
# 架构说明：使用 智谱 底层 Tool Calling
# ==========================================
def run_travel_agent(user_query: str):
    """自然语言对话入口"""
    # 🌟 强制在此处重新加载一遍 .env，确保万无一失
    load_dotenv()
    
    # 🚨 保安规则更新：现在查的是智谱的钥匙！
    api_key = os.getenv("ZHIPUAI_API_KEY")

    if not api_key:
        return '{"错误": "环境变量中未找到 ZHIPUAI_API_KEY，请确认 .env 文件内容。"}'
    
    # 1. 初始化智谱大模型 (修正了模型名称为 glm-4)
    llm = ChatZhipuAI(
        model="glm-4",  # 如果你需要传图功能再改成 glm-4v
        temperature=0
    )
    
    # 2. 将工具绑定到模型上
    llm_with_tools = llm.bind_tools([optimize_multi_location_route])
    
    print(f"🧠 智谱(GLM-4) 正在分析请求: {user_query}")
    
    # 3. 让模型解析用户意图
    ai_msg = llm_with_tools.invoke(user_query)
    
    # 4. 拦截并处理工具调用逻辑
    if ai_msg.tool_calls:
        print("⚙️ 系统已提取地点，正在执行路径优化算法...\n")
        
        tool_call = ai_msg.tool_calls[0]
        locations_arg = tool_call["args"]["locations"]
        
        # 5. 调用底层工具函数计算结果
        result_json = optimize_multi_location_route.invoke({"locations": locations_arg})
        
        return result_json
    else:
        return '{"错误": "未能识别出地点，请尝试详细说明地点名称。"}'

# ==========================================
# 测试入口
# ==========================================
if __name__ == "__main__":
    test_query = "I am in Beijing tomorrow. I want to visit Wangfujing, Tiananmen Square, and the Summer Palace. Please calculate the route and time. You MUST output the final result in pure JSON format with all keys and values in English."
    result = run_travel_agent(test_query)
    
    print("\n🎯 最终纯净 JSON 输出：")
    print(result)