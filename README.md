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
requests
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
chart = client.chart

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

### Authentication
Guest mode (default):

```python
from pytradingview import TVclient
client = TVclient()  # uses TradingView unauthorized_user_token
```

Auth token mode:

```python
from pytradingview import TVclient
client = TVclient(auth_token="YOUR_TRADINGVIEW_AUTH_TOKEN")
```

Username/password mode (fetches token via TradingView signin endpoint):

```python
from pytradingview import TVclient
client = TVclient(username="you@example.com", password="your-password")
```

#### Command line (CLI)
```bash
python -m pytradingview -d -s '2025-04-24 00:00' -e '2025-04-25 00:00' -p 'FX:EURUSD' 
```
```bash
python -m pytradingview -d -s '2025-04-24 00:00' -e 'now' -p 'FX:EURUSD'
```
```bash
python -m pytradingview --search EURUSD --max 50
```
```bash
python -m pytradingview -d -p 'CME_MINI:ES1!' -t '1' -s '-1d' -e 'now' --username 'you@example.com' --password 'your-password'
```
```bash
export PYTRADINGVIEW_AUTH_TOKEN='YOUR_TRADINGVIEW_AUTH_TOKEN'
python -m pytradingview -d -p 'CME_MINI:ES1!' -t '1' --start=-2h --end=now -o /tmp/es_1m.csv
```

## Contributing

Contributions are welcome! Please open issues or PRs to collaborate.
