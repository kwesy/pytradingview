#!/usr/bin/env python3
"""
Stream quote (last-price) updates from TradingView and print to console.
"""

import argparse
import os
import threading
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import certifi

from pytradingview import TVclient

AUTH_TOKEN_ENV_VARS = ("PYTRADINGVIEW_AUTH_TOKEN", "TV_AUTH_TOKEN")
DEFAULT_SYMBOLS = "CME_MINI:ES1!,CME_MINI:NQ1!,COMEX:GC1!,NYMEX:CL1!,COMEX:SI1!,CBOT_MINI:YM1!,CME_MINI:RTY1!"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Stream and print quote updates (lp/lp_time) from TradingView websocket."
    )
    parser.add_argument(
        "--symbols",
        default=DEFAULT_SYMBOLS,
        help="Comma-separated TradingView symbols",
    )
    parser.add_argument(
        "--auth-token",
        default=None,
        help="TradingView auth token (env fallback: PYTRADINGVIEW_AUTH_TOKEN or TV_AUTH_TOKEN)",
    )
    parser.add_argument(
        "--timezone",
        default="America/New_York",
        help="Display timezone, e.g. America/New_York or UTC",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=0,
        help="Stop after N seconds (0 = no timeout).",
    )
    return parser.parse_args()


def resolve_auth_token(cli_token):
    for env_var in AUTH_TOKEN_ENV_VARS:
        token = os.getenv(env_var)
        if token:
            return token
    return cli_token


def format_epoch(epoch_seconds, tz_name):
    if epoch_seconds is None:
        return "n/a"
    tz = ZoneInfo(tz_name)
    dt_utc = datetime.fromtimestamp(int(float(epoch_seconds)), tz=timezone.utc)
    return dt_utc.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S %Z")


def main():
    args = parse_args()
    auth_token = resolve_auth_token(args.auth_token)
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    if not symbols:
        raise SystemExit("No symbols provided")

    if not os.getenv("SSL_CERT_FILE"):
        os.environ["SSL_CERT_FILE"] = certifi.where()

    client = TVclient(auth_token=auth_token)
    quote = client.quote

    def stop(reason):
        print(f"[stop] {reason}")
        try:
            client.end(lambda: None)
        except Exception:
            pass

    def on_connected(_):
        print(f"[connected] quote symbols={','.join(symbols)}")

    def on_error(err):
        print(f"[error] {err}")

    def make_handler(symbol):
        def handle(packet):
            if packet["type"] == "quote_completed":
                print(f"[quote_ready] symbol={symbol}")
                return

            if packet["type"] != "qsd":
                return

            payload = packet["data"][1]
            values = payload.get("v", {})
            lp = values.get("lp")
            lp_time = values.get("lp_time")
            bid = values.get("bid")
            ask = values.get("ask")
            volume = values.get("volume")

            recv_ts = datetime.now(timezone.utc).astimezone(ZoneInfo(args.timezone)).strftime(
                "%Y-%m-%d %H:%M:%S %Z"
            )
            print(
                f"[quote] symbol={symbol} recv={recv_ts} "
                f"lp={lp} lp_time={format_epoch(lp_time, args.timezone)} "
                f"bid={bid} ask={ask} volume={volume}"
            )

        return handle

    client.on_connected(on_connected)
    client.on_error(on_error)

    quote.set_up_quote({"customFields": ["lp", "lp_time", "bid", "ask", "volume"]})
    for symbol in symbols:
        quote.on_symbol(symbol, make_handler(symbol))
    quote.add_symbols(symbols, fast=True, force_permission=True)

    if args.timeout_seconds > 0:
        timer = threading.Timer(args.timeout_seconds, lambda: stop("timeout reached"))
        timer.daemon = True
        timer.start()

    client.create_connection()


if __name__ == "__main__":
    main()
