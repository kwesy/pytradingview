# pytradingview

A lightweight, open-source Python client for connecting to TradingView's WebSocket API.

## Features

- WebSocket connection management
- Easy to extend for custom signals and data
- Download data
- Search for symbols

## Dependencies
```bash
websocket-client
```

## Installation

```bash
pip install pytradingview
```

## Usage
```python
# example.py
from pytradingview import TVclient

# Create the client and chart
client = TVclient()
chart = client.Chart

# Set up the chart
chart.set_up_chart()

# Set the market
chart.set_market("BINANCE:BTCUSD", {
    "timeframe": "1",  # 1-minute chart
    "currency": "USD",
})

# Event: When the symbol data is loaded
chart.on_symbol_loaded(lambda _: print("✅ Market loaded:", chart.get_infos['description']))

# Event: When price data is updated
def handle_update(_):
    if chart.get_periods:
        print(f"🟢 New Price: {chart.get_periods['close']}")

chart.on_update(handle_update)

# Start the WebSocket connection
client.create_connection()
```

#### Command line (CLI)
```bash
python -m pytradingview -d -s '2025-04-24 00:00' -e '2025-04-25 00:00' -p 'FX:EURUSD' 
```
```bash
python -m pytradingview --search EURUSD --max 50
```

## Contributing

Contributions are welcome! Please open issues or PRs to collaborate.
