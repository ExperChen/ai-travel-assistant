import json
import threading
from pathlib import Path
from typing import Any

from langchain.tools import tool

# 导入我们刚才写好的底层查询逻辑
from .transportation_info_provider import fetch_transport_details

# 定义交通工具的专属缓存文件路径
_CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "transport_cache.json"
_CACHE_LOCK = threading.Lock()

def _load_cache() -> dict[str, dict[str, Any]]:
    """加载本地缓存文件"""
    if not _CACHE_PATH.exists():
        # 如果 data 文件夹不存在，自动创建
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        return {}
    try:
        return json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _save_cache(cache: dict[str, dict[str, Any]]) -> None:
    """保存数据到本地缓存文件"""
    _CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

@tool
def transportation_tool(origin: str, destination: str, transport_mode: str = "transit") -> dict[str, Any]:
    """
    交通信息工具：返回从出发地到目的地的预估耗时、当地价格及参考来源。
    注意：此工具返回的价格通常为目的地的当地货币（如去日本返回日元，去英国返回英镑，在马来西亚返回马币）。
    如果用户需要统一以马币 (MYR) 报价，请在获得此工具结果后，由大模型Agent自行进行汇率换算。

    Args:
        origin: 出发地，例如 "Narita Airport", "KLIA", "Paris"
        destination: 目的地，例如 "Tokyo Station", "KLCC", "London"
        transport_mode: 交通方式，推荐使用 "transit" (公共交通/地铁/火车), "driving" (打车/开车)
    """
    # 1. 构造唯一的缓存 Key (统一转小写，防止大小写导致缓存未命中)
    cache_key = f"{origin.strip().lower()}::to::{destination.strip().lower()}::via::{transport_mode.strip().lower()}"

    # 2. 加锁读取缓存，看是否之前查过这条路线
    with _CACHE_LOCK:
        cache = _load_cache()
        if cache_key in cache:
            # 命中缓存！直接返回，不花 SerpApi 的钱
            return cache[cache_key]

    # 3. 如果没查过，调用 Provider 去网上真实查询
    result = fetch_transport_details(origin=origin, destination=destination, transport_mode=transport_mode)

    # 4. 把查到的新结果写进缓存，方便下次直接用
    with _CACHE_LOCK:
        cache = _load_cache()
        cache[cache_key] = result
        _save_cache(cache)

    return result
