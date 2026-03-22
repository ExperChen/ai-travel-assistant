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
    load_dotenv()
    
    api_key = os.getenv("ZHIPUAI_API_KEY")
    if not api_key:
        return '{"error": "ZHIPUAI_API_KEY not found in .env"}'
    
    # 1. 初始化智谱大模型
    llm = ChatZhipuAI(model="glm-4", temperature=0)
    llm_with_tools = llm.bind_tools([optimize_multi_location_route])
    
    print(f" 智谱(GLM-4) 正在分析请求...")
    
    # 2. 让模型解析用户意图，决定是否调用工具
    ai_msg = llm_with_tools.invoke(user_query)
    
    if ai_msg.tool_calls:
        print(" 系统已提取地点，正在执行底层算法...\n")
        tool_call = ai_msg.tool_calls[0]
        locations_arg = tool_call["args"]["locations"]
        
        # 3. 调用底层工具（拿到的是中文硬编码结果）
        raw_chinese_result = optimize_multi_location_route.invoke({"locations": locations_arg})
        
        # 🌟 4. 核心修复：把中文结果丢回给大脑，强制要求全英文翻译！
        print(" 正在将计算结果转换为纯英文 JSON...")
        translation_prompt = f"""
        Here is the raw route calculation result: {raw_chinese_result}
        CRITICAL INSTRUCTION: 
        1. Translate ALL information (keys and values) into professional English.
        2. Output ONLY a valid, pure JSON object. Absolutely NO markdown formatting blocks like ```json and NO extra text.
        """
        
        # 让大脑做最后一步翻译工作
        final_msg = llm.invoke(translation_prompt)
        
        return final_msg.content
    else:
        return '{"error": "Failed to extract locations from your query."}'

# ==========================================
# 测试入口
# ==========================================
if __name__ == "__main__":
    test_query = "I am in Beijing tomorrow. I want to visit Wangfujing, Tiananmen Square, and the Summer Palace. Please calculate the route and time."
    result = run_travel_agent(test_query)
    
    print("\n 最终纯净 JSON 输出：")
    print(result)