# multi_route_tool.py
import os
import json
import itertools
from serpapi import GoogleSearch
from langchain_core.tools import tool

def _get_route_edge(origin: str, destination: str, api_key: str) -> dict:
    # ... (这里是我刚才给你的提取秒数、不要 Emoji 的干净底层代码) ...
    pass

@tool
def optimize_multi_location_route(locations: list[str]) -> str:
    # ... (这里是我给你的全排列算法，最后返回 ensure_ascii=False 的纯中文 JSON) ...
    pass