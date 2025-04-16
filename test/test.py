# tests/test_client.py

from pytradingview.client import TradingViewClient

def test_client_connect():
    client = TradingViewClient()
    assert client.url.startswith("wss://")
