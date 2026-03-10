from pathlib import Path
import sys

# 1. Dynamically load the app/tools directory to ensure the test file can find hotel_tool.py
TOOLS_DIR = Path(__file__).resolve().parents[1] / "app" / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.append(str(TOOLS_DIR))

import hotel_tool

def test_search_hotels_without_api_key_returns_error(monkeypatch):
    """
    Test scenario: If SERPAPI_API_KEY is not configured, the program should return a specific error message instead of crashing.
    """
    # Use pytest's monkeypatch to temporarily delete the API Key from environment variables
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    
    # Simulate the AI calling your tool
    result = hotel_tool.search_hotels("Tokyo", "2026-05-01", "2026-05-05")
    
    # Start assertions (check if the result matches expectations)
    assert isinstance(result, list)  # Must return a list
    assert len(result) > 0           # List cannot be empty
    assert "error" in result[0]      # The first result must contain the "error" key
    assert "SERPAPI_API_KEY" in result[0]["error"]  # The error message must mention the missing API Key