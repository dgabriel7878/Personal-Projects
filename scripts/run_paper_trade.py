#!/usr/bin/env python3
"""Run one daily Supertrend paper-trading reconciliation cycle against
Alpaca for each given symbol: buy if the signal just turned long and
there's no position, close if it turned flat and there is one, otherwise
do nothing. Meant to be run once per trading day (see README for how to
schedule it), not left running continuously.

Requires ALPACA_API_KEY and ALPACA_SECRET_KEY in the environment -- copy
.env.example to .env and fill in your Alpaca **paper trading** keys.

Examples:
    python scripts/run_paper_trade.py --symbols AAPL MSFT SPY QQQ
    python scripts/run_paper_trade.py --symbols AAPL --dry-run
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from trading_bot.config import UNIVERSE
from trading_bot.execution.alpaca_trader import reconcile


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=UNIVERSE["stocks"],
        help="Stock/ETF tickers to trade (default: the configured stock universe).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute signals and print what would happen, without placing any orders.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if "ALPACA_API_KEY" not in os.environ or "ALPACA_SECRET_KEY" not in os.environ:
        print(
            "Missing ALPACA_API_KEY / ALPACA_SECRET_KEY.\n"
            "Copy .env.example to .env and fill in your paper trading keys from "
            "https://app.alpaca.markets/paper/dashboard/overview"
        )
        sys.exit(1)

    for symbol in args.symbols:
        try:
            print(reconcile(symbol, dry_run=args.dry_run))
        except Exception as exc:
            print(f"{symbol}: ERROR - {exc}")


if __name__ == "__main__":
    main()
