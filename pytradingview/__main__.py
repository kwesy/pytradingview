import argparse
import sys
from .utils import parse_datetime


def parse_args():
    parser = argparse.ArgumentParser(prog='pytradingview.py' ,description="Download historical candle data")
    parser.add_argument('-p', '--symbol', type=str, help="Instrument or trading pair you want to download")
    parser.add_argument('-t', '--timeframe', type=str, help="Set chart timeframe. eg '1', '5', '15', '60', 'D' etc. Default is '5' for 5 minuite chart frame", default="5")
    parser.add_argument('-d', '--download', action='store_true', help="Download data")
    parser.add_argument('-s', '--start', type=str, help="Start date (absolute or relative, e.g. 'YYYY-MM-DD', 'YYY-MM-DD HH:MM', 'YYYY-MM-DDTHH:MM', 'now', '-7d')")
    parser.add_argument('-e', '--end', type=str, help="End date (absolute or relative, e.g. 'YYYY-MM-DD', 'YYY-MM-DD HH:MM', 'YYYY-MM-DDTHH:MM', 'now', '-7d')")
    parser.add_argument('-u', '--currency', type=str, help="Set unit of currency. Default is 'USD'", default="USD")
    parser.add_argument('-o', '--output', type=str, help="Output filename.", default="output.csv")
    parser.add_argument('--search', help="Search for symbol using TradingView's symbol search")
    parser.add_argument('--max', type=int, default=50, help="Maximum number of results to return from search (default: 50)")
    parser.add_argument('--auth-token', type=str, help="TradingView auth token")
    parser.add_argument('--username', type=str, help="TradingView username/email")
    parser.add_argument('--password', type=str, help="TradingView password")

    # Show help if no arguments are provided
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    return parser.parse_args()

def main():

    from pytradingview import TVclient

    args = parse_args()

    client = TVclient(
        auth_token=args.auth_token,
        username=args.username,
        password=args.password,
    )
    chart = client.chart

    if args.download:
        start = parse_datetime(args.start)
        end = parse_datetime(args.end)

        # Set up the chart
        chart.set_up_chart()

        # Set the market
        chart.set_market(args.symbol, {
            "timeframe": args.timeframe,
            "currency": args.currency,
        })

        # Event: When the symbol data is loaded
        chart.on_symbol_loaded(lambda _: print("✅ Market loaded:", chart.get_infos['description']))

        client.on_connected(lambda _ : chart.download_data(start=start, end=end, filename=args.output))

        # Start the WebSocket connection
        client.create_connection()

    if args.search:
        result = chart.search_symbols(args.search, args.max)
        print(f"on Results for \"{args.search}\" ({len(result)}):")
        for item in sorted(result, key=lambda x: x['symbol']):
            print(f"- {item['symbol']} ({item['description']}) [{item['type']}]")
        sys.exit(0)

if __name__ == "__main__":
    main()
