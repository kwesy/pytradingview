import argparse
import datetime
import sys


def parse_args():
    parser = argparse.ArgumentParser(prog='pytradingview.py' ,description="Download historical candle data")
    parser.add_argument('-p', '--symbol', type=str, help="Instrument or trading pair you want to download")
    parser.add_argument('-t', '--timeframe', type=str, help="Set chart timeframe. eg '1', '5', '15', '60', 'D' etc. Default is '5' for 5 minuite chart frame", default="5")
    parser.add_argument('-d', '--download', action='store_true', help="Download data")
    parser.add_argument('-s', '--start', type=str, help="Start date (YYYY-MM-DD HH:MM)")
    parser.add_argument('-e', '--end', type=str, help="End date (YYYY-MM-DD HH:MM)")
    parser.add_argument('-u', '--currency', type=str, help="Set unit of currency. Default is 'USD'", default="USD")
    parser.add_argument('-o', '--output', type=str, help="Output filename.", default="output.csv")

    # Show help if no arguments are provided
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    return parser.parse_args()

def main():

    args = parse_args()

    if args.download:
        try:
            start = datetime.datetime.strptime(args.start, "%Y-%m-%d %H:%M")
            end = datetime.datetime.strptime(args.end, "%Y-%m-%d %H:%M")
        except ValueError:
            print("⚠️ Invalid datetime format. Use: YYYY-MM-DD HH:MM (e.g., '2025-05-20 08:00')")
            return

        from pytradingview import TVclient

        client = TVclient()
        chart = client.chart

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

if __name__ == "__main__":
    main()
