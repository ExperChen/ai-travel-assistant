from dotenv import load_dotenv
import os
from pathlib import Path
import sys
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, AIMessagePromptTemplate
from langchain_core.runnables import RunnableLambda

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.append(str(TOOLS_DIR))

from attraction_tool import attraction_information_tool

load_dotenv()

def _is_quota_exhausted_error(exc: Exception) -> bool:
    text = str(exc)
    return (
        "RESOURCE_EXHAUSTED" in text
        or "Quota exceeded" in text
        or "You exceeded your current quota" in text
        or "generate_content_free_tier_requests" in text
    )

def _build_llm(use_google: bool):
    if use_google and os.getenv("GOOGLE_API_KEY"):
        return ChatGoogleGenerativeAI(
            model=os.getenv("GOOGLE_LLM_MODEL", "gemini-2.5-flash"),
            api_key=os.getenv("GOOGLE_API_KEY"),
        )
    return ChatOpenAI(
        model=os.getenv("COMPANY_LLM_MODEL", "gpt-4o-mini"),
        base_url=os.getenv("COMPANY_BASE_URL"),
        api_key=os.getenv("COMPANY_API_KEY"),
    )

use_google = bool(os.getenv("GOOGLE_API_KEY"))
llm = _build_llm(use_google)








# 定义系统提示
system_prompt = f"""
你是一名专业的 AI 旅游规划助手，负责帮助用户制定简单、清晰、实用的旅游计划。
    你的目标是根据用户提供的信息，查询目的地景点，并生成合理的游玩建议。
    【工作流程】
    1. 当用户提出旅游需求时，你必须先确认以下信息：
    * 用户当前所在城市
    * 旅游目的地
    * 旅游时间（几天或具体日期）
    * 预算范围
    2. 如果信息不完整，请主动向用户提问补充信息，不要直接生成计划。
    3. 当获得完整信息后，调用工具查询：
    * 目的地可游玩的景点
    * 每个景点的门票价格
    * 建议游玩时间
    * 景点所在位置
    4. 根据查询结果进行整理，筛选：
    * 符合用户预算的景点
    * 在旅游时间内可以完成的景点
    5. 根据景点建议游玩时间，生成简单的行程建议。
    【调用工具规则】
    当需要获取景点信息时，必须调用工具[attraction_information_tool]，而不是自己编造数据。
    工具需要返回以下信息：
    * 景点名称
    * 门票价格
    * 建议游玩时间
    * 地址或位置
    【输出内容要求】
    最终输出应包含：
    1. 推荐景点列表
    2. 每个景点的门票价格
    3. 建议游玩时长
    4. 简单的游玩顺序建议
    输出示例：
    推荐景点：
    1. 景点A
    门票：RM50
    建议游玩时间：2小时
    2. 景点B
    门票：RM30
    建议游玩时间：1.5小时
    行程建议：
    Day 1：景点A → 景点B

    回答要清晰、简洁、实用。
"""
# 定义用户输入模板
human_message = HumanMessagePromptTemplate.from_template("""
{input}
""")
# 定义AI回复模板并存储聊天记录
# agent_scratchpad 用于存储中间结果
ai_message = AIMessagePromptTemplate.from_template("""
{agent_scratchpad}
""")
chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        human_message,
        ai_message,
    ]
)
preview_messages = chat_prompt.format_messages(input="帮我规划吉隆坡2天行程", agent_scratchpad="")
print(f"Prompt消息条数: {len(preview_messages)}")

agent = create_agent(
    llm,
    tools=[attraction_information_tool],
    system_prompt=system_prompt, # 不需要换成chat_prompt

)












print("AI Travel Assistant 已启动，输入 exit 退出。")
while True:
    text = input("旅行请求: ").strip()
    if not text:
        continue
    if text.lower() == "exit":
        print("已退出。")
        break
    try:
        result = agent.invoke({"messages": [("user", text)]})
        messages = result.get("messages", [])
        output = messages[-1].content if messages else "无回复"
        # message[-1] 是最后一条消息，通常是 AI 回复

    except Exception as e:
        if use_google and _is_quota_exhausted_error(e):
            use_google = False
            llm = _build_llm(use_google)
            agent = create_agent(
                llm,
                tools=[attraction_information_tool],
                system_prompt=system_prompt,
            )
            result = agent.invoke({"messages": [("user", text)]})
            messages = result.get("messages", [])
            output = messages[-1].content if messages else "无回复"
        else:
            output = f"调用失败: {e}"
    print("\n=== 旅行规划结果 ===")
    print(output)
    print("====================\n")
