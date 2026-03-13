import json
import os
import sys
import importlib.util
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]
TARGET_SCRIPT = BASE_DIR / "app" / "tests" / "test_hotel_agent_json_with_tool_output.py"
TARGET_OUTPUT = BASE_DIR / "app" / "tests" / "hotel_agent_with_tool_output.json"

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
            temperature=0.2,
        )
    return ChatOpenAI(
        model=os.getenv("COMPANY_LLM_MODEL", "gpt-4o-mini"),
        base_url=os.getenv("COMPANY_BASE_URL"),
        api_key=os.getenv("COMPANY_API_KEY"),
        temperature=0.2,
    )

def _build_agent(use_google: bool):
    llm = _build_llm(use_google)
    return create_agent(
        model=llm,
        tools=[run_hotel_script, read_hotel_output],
        system_prompt=(
            "你是酒店结果整理助手。"
            "你必须先调用 run_hotel_script 再调用 read_hotel_output。"
            "最终只输出酒店名称、numeric price、rating、address、官网、图片。"
        ),
    )


@tool
def run_hotel_script(query: str) -> str:
    """运行酒店脚本并写出 JSON 输出文件。"""
    spec = importlib.util.spec_from_file_location("hotel_agent_json_runner", str(TARGET_SCRIPT))
    if spec is None or spec.loader is None:
        return f"加载脚本失败: {TARGET_SCRIPT}"
    module = importlib.util.module_from_spec(spec)
    sys.modules["hotel_agent_json_runner"] = module
    spec.loader.exec_module(module)
    saved_path = module.run_hotel_agent_and_save_json(query)
    return f"脚本已执行，输出文件: {saved_path}"


@tool
def read_hotel_output() -> str:
    """读取酒店 JSON 输出并按指定字段格式化为文本。"""
    if not TARGET_OUTPUT.exists():
        return f"未找到输出文件: {TARGET_OUTPUT}"
    with open(TARGET_OUTPUT, "r", encoding="utf-8") as file:
        payload = json.load(file)

    rows: list[str] = []
    tool_outputs = payload.get("tool_outputs", [])
    for item in tool_outputs:
        content = item.get("content", [])
        if not isinstance(content, list):
            continue
        for hotel in content:
            rows.append(
                "\n".join(
                    [
                        f"酒店名称: {hotel.get('name', '')}",
                        f"numeric price: {hotel.get('numeric_price', '')}",
                        f"rating: {hotel.get('rating', '')}",
                        f"address: {hotel.get('address', '')}",
                        f"官网: {hotel.get('hotel_source_url', '')}",
                        f"图片: {hotel.get('image_url', '')}",
                    ]
                )
            )
    if not rows:
        return "输出文件存在，但未解析到酒店列表。"
    return "\n\n".join(rows)

use_google = bool(os.getenv("GOOGLE_API_KEY"))
agent = _build_agent(use_google)


if __name__ == "__main__":
    print("Hotel Agent 已启动，输入 exit 退出。")
    while True:
        text = input("请求: ").strip()
        if not text:
            continue
        if text.lower() == "exit":
            print("已退出。")
            break
        try:
            result = agent.invoke({"messages": [{"role": "user", "content": text}]})
        except Exception as e:
            if use_google and _is_quota_exhausted_error(e):
                use_google = False
                agent = _build_agent(use_google)
                result = agent.invoke({"messages": [{"role": "user", "content": text}]})
            else:
                raise
        messages = result.get("messages", [])
        output = messages[-1].content if messages else "无回复"
        print("\n=== 酒店结果 ===")
        print(output)
        print("================\n")
