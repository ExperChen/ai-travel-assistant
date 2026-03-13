import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

TOOLS_DIR = Path(__file__).resolve().parents[2]
if str(TOOLS_DIR) not in sys.path:
    sys.path.append(str(TOOLS_DIR))

from app.tools.hotel_tool import search_hotels

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
            temperature=0.2,
        )
    return ChatOpenAI(
        model=os.getenv("COMPANY_LLM_MODEL", "gpt-4o-mini"),
        base_url=os.getenv("COMPANY_BASE_URL"),
        api_key=os.getenv("COMPANY_API_KEY"),
        temperature=0.2,
    )


def _extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content.replace("\\n", "\n")
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text", "")))
            else:
                parts.append(str(item))
        return "".join(parts).replace("\\n", "\n")
    return str(content).replace("\\n", "\n")


def _to_json_value(content: Any) -> Any:
    if isinstance(content, (dict, list, int, float, bool)) or content is None:
        return content
    if isinstance(content, str):
        text = content.strip()
        if not text:
            return ""
        try:
            return json.loads(text)
        except Exception:
            return text
    return str(content)


def run_hotel_agent_and_save_json(user_query: str) -> Path:
    use_google = bool(os.getenv("GOOGLE_API_KEY"))
    llm = _build_llm(use_google)

    system_prompt = """You are a premium travel consultant.
Your task is to fetch hotel data using tools, then filter them strictly based on user requirements.
Always provide: Hotel Name, Price, Rating, Address, and a compelling reason for recommendation."""

    agent_executor = create_agent(
        model=llm,
        tools=[search_hotels],
        system_prompt=system_prompt,
    )

    try:
        result = agent_executor.invoke({"messages": [{"role": "user", "content": user_query}]})
    except Exception as e:
        if use_google and _is_quota_exhausted_error(e):
            llm = _build_llm(False)
            agent_executor = create_agent(
                model=llm,
                tools=[search_hotels],
                system_prompt=system_prompt,
            )
            result = agent_executor.invoke({"messages": [{"role": "user", "content": user_query}]})
        else:
            raise
    messages = result.get("messages", [])
    final_answer = _extract_text(messages[-1].content if messages else "")

    tool_calls: list[dict[str, Any]] = []
    tool_outputs: list[dict[str, Any]] = []

    for msg in messages:
        msg_type = getattr(msg, "type", "")
        if msg_type == "ai":
            for call in getattr(msg, "tool_calls", []) or []:
                tool_calls.append(
                    {
                        "id": call.get("id"),
                        "name": call.get("name"),
                        "args": call.get("args"),
                    }
                )
        if msg_type == "tool":
            tool_outputs.append(
                {
                    "tool_name": getattr(msg, "name", ""),
                    "tool_call_id": getattr(msg, "tool_call_id", ""),
                    "content": _to_json_value(getattr(msg, "content", "")),
                }
            )

    payload = {
        "query": user_query,
        "final_answer": final_answer,
        "tool_calls": tool_calls,
        "tool_outputs": tool_outputs,
    }

    output_path = Path(__file__).resolve().parent / "hotel_agent_with_tool_output.json"
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
    return output_path


if __name__ == "__main__":
    query = "Help me find 3 high-rated hotels in Penang for 2026-05-01 to 2026-05-05, under RM 300 per night. Show addresses."
    saved_path = run_hotel_agent_and_save_json(query)
    print(f"JSON output saved to: {saved_path}")
