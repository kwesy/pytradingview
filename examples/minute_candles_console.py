#!/usr/bin/env python3
"""
Stream 1-minute candles from TradingView and print them to console.
"""

import argparse
import os
import threading
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import certifi

from pytradingview import TVclient
from pytradingview.chart import ChartSession

AUTH_TOKEN_ENV_VARS = ("PYTRADINGVIEW_AUTH_TOKEN", "TV_AUTH_TOKEN")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Stream and print 1-minute candles from TradingView websocket."
    )
    parser.add_argument(
        "--symbols",
        default="CME_MINI:ES1!",
        help="Comma-separated TradingView symbols",
    )
    parser.add_argument("--currency", default="USD", help="Currency code")
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
        "--max-closed-bars",
        type=int,
        default=0,
        help="Stop after N closed bars (0 = run until Ctrl+C).",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=0,
        help="Stop after N seconds (0 = no timeout).",
    )
    parser.add_argument(
        "--print-forming",
        action="store_true",
        help="Also print updates for the currently forming minute bar.",
    )
    return parser.parse_args()


def resolve_auth_token(cli_token):
    for env_var in AUTH_TOKEN_ENV_VARS:
        token = os.getenv(env_var)
        if token:
            return token
    return cli_token


def to_display_ts(epoch_seconds, tz_name):
    tz = ZoneInfo(tz_name)
    dt_utc = datetime.fromtimestamp(int(float(epoch_seconds)), tz=timezone.utc)
    dt_local = dt_utc.astimezone(tz)
    return dt_local.strftime("%Y-%m-%d %H:%M:%S %Z")


def format_candle(candle, tz_name):
    return (
        f"time={to_display_ts(candle['time'], tz_name)} "
        f"o={candle['open']} h={candle['high']} "
        f"l={candle['low']} c={candle['close']} v={candle['volume']}"
    )


def main():
    args = parse_args()
    auth_token = resolve_auth_token(args.auth_token)

    if not os.getenv("SSL_CERT_FILE"):
        os.environ["SSL_CERT_FILE"] = certifi.where()

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    if not symbols:
        raise SystemExit("No symbols provided")

    client = TVclient(auth_token=auth_token)
    states = {
        symbol: {"last_candle": None, "closed_count": 0, "done": False}
        for symbol in symbols
    }

    def stop(reason):
        print(f"[stop] {reason}")
        try:
            client.end(lambda: None)
        except Exception:
            pass

    def on_connected(_):
        print(f"[connected] symbols={','.join(symbols)} timeframe=1")

    def on_error(err):
        print(f"[error] {err}")

    def make_on_symbol_loaded(symbol, chart):
        def on_symbol_loaded(_):
            desc = chart.get_infos.get("description", "")
            print(f"[symbol_loaded] symbol={symbol} description={desc}")
        return on_symbol_loaded

    def maybe_stop_after_max():
        if args.max_closed_bars <= 0:
            return
        all_done = all(states[symbol]["done"] for symbol in symbols)
        if all_done:
            stop(f"max closed bars reached for all symbols ({args.max_closed_bars})")

    def make_on_update(symbol, chart):
        def on_update(_):
            state = states[symbol]
            candle = chart.get_periods
            if not candle:
                return

            if state["last_candle"] is None:
                state["last_candle"] = dict(candle)
                print(f"[forming] symbol={symbol} {format_candle(candle, args.timezone)}")
                return

            prev = state["last_candle"]
            prev_ts = int(float(prev["time"]))
            cur_ts = int(float(candle["time"]))

            if cur_ts != prev_ts:
                print(f"[closed]  symbol={symbol} {format_candle(prev, args.timezone)}")
                state["closed_count"] += 1
                if (
                    args.max_closed_bars > 0
                    and state["closed_count"] >= args.max_closed_bars
                    and not state["done"]
                ):
                    state["done"] = True
                    maybe_stop_after_max()

            if args.print_forming:
                print(f"[forming] symbol={symbol} {format_candle(candle, args.timezone)}")

            state["last_candle"] = dict(candle)

        return on_update

    client.on_connected(on_connected)
    client.on_error(on_error)

    charts = []
    for idx, symbol in enumerate(symbols):
        chart = client.chart if idx == 0 else ChartSession(client.get_client_brigde)
        charts.append(chart)
        chart.on_symbol_loaded(make_on_symbol_loaded(symbol, chart))
        chart.on_update(make_on_update(symbol, chart))
        chart.set_up_chart()
        chart.set_market(
            symbol,
            {
                "timeframe": "1",
                "currency": args.currency,
            },
        )

    if args.timeout_seconds > 0:
        timer = threading.Timer(args.timeout_seconds, lambda: stop("timeout reached"))
        timer.daemon = True
        timer.start()

    client.create_connection()


if __name__ == "__main__":
    main()
