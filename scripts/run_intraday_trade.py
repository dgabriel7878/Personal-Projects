#!/usr/bin/env python3
"""Run one intraday paper-trading reconciliation cycle against Alpaca for
each given symbol, using either the VWAP or RSI mean-reversion strategy
(long AND short). Unlike run_paper_trade.py (once daily), this is meant
to be invoked every few minutes throughout market hours -- see README for
how to schedule it. It flattens any open position as the close approaches
regardless of signal, so it never holds overnight.

Requires ALPACA_API_KEY and ALPACA_SECRET_KEY in the environment -- copy
.env.example to .env and fill in your Alpaca **paper trading** keys.

Examples:
    python scripts/run_intraday_trade.py --symbols AAPL MSFT --strategy vwap
    python scripts/run_intraday_trade.py --symbols AAPL --strategy rsi --dry-run
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from trading_bot.config import UNIVERSE
from trading_bot.execution.intraday_trader import DECISION_FUNCS, get_client, get_market_clock, reconcile


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=UNIVERSE["stocks"],
        help="Stock/ETF tickers to trade (default: the configured stock universe).",
    )
    parser.add_argument(
        "--strategy",
        choices=list(DECISION_FUNCS),
        default="vwap",
        help="Which intraday strategy to trade (default: vwap).",
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

    client = get_client()
    clock = get_market_clock(client)
    if not clock.is_open:
        print(f"Market is closed (next open: {clock.next_open}). Nothing to do -- exiting.")
        return

    # Each new entry alone would otherwise be sized against the FULL
    # account (tight intraday stops mean the leverage cap, not the risk
    # target, usually decides the size -- see risk_based_size's
    # docstring). Splitting it evenly across the symbols in this batch
    # keeps the batch as a whole from wanting more capital than exists,
    # even if several signal on the same run.
    max_leverage = 1.0 / len(args.symbols)

    for symbol in args.symbols:
        try:
            print(
                reconcile(
                    symbol,
                    strategy=args.strategy,
                    max_leverage=max_leverage,
                    dry_run=args.dry_run,
                    client=client,
                    clock=clock,
                )
            )
        except Exception as exc:
            print(f"{symbol}: ERROR - {exc}")


if __name__ == "__main__":
    main()
