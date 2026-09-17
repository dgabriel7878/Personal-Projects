#!/usr/bin/env python3
"""Walk-forward validation for one strategy: optimize its parameters on the
first `--train-frac` of each ticker's history, then run those parameters
unmodified on the held-out remainder, so you can see whether a strategy's
edge survives on data it never saw.

Example:
    python scripts/validate_strategy.py --strategy "Donchian Breakout" --tickers AAPL SPY QQQ
    python scripts/validate_strategy.py --strategy "RSI Mean Reversion" --tickers AAPL MSFT SPY --train-frac 0.6
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from tabulate import tabulate

from trading_bot.backtest.validate import PARAM_GRIDS, walk_forward
from trading_bot.config import DEFAULT_CASH, DEFAULT_COMMISSION, UNIVERSE
from trading_bot.strategies import STRATEGY_REGISTRY

pd.set_option("display.width", 140)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strategy",
        required=True,
        choices=[name for name, cls, _ in STRATEGY_REGISTRY if cls in PARAM_GRIDS],
        help="Which strategy to validate.",
    )
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=[t for tickers in UNIVERSE.values() for t in tickers],
        help="Tickers to test (default: the full configured universe).",
    )
    parser.add_argument(
        "--train-frac",
        type=float,
        default=0.7,
        help="Fraction of each ticker's history used for in-sample optimization (default: 0.7).",
    )
    parser.add_argument("--cash", type=float, default=DEFAULT_CASH)
    parser.add_argument("--commission", type=float, default=DEFAULT_COMMISSION)
    return parser.parse_args()


def main():
    args = parse_args()
    print(
        f"Walk-forward validating {args.strategy!r} on {args.tickers} "
        f"(train_frac={args.train_frac})\n"
    )

    results = walk_forward(
        args.strategy,
        args.tickers,
        train_frac=args.train_frac,
        cash=args.cash,
        commission=args.commission,
    )

    if results.empty:
        print("No results -- check data availability and try again.")
        return

    print(tabulate(results, headers="keys", tablefmt="github", showindex=False, floatfmt=".2f"))

    positive_oos = (results["Test Sharpe"] > 0).sum()
    print(
        f"\n{positive_oos}/{len(results)} tickers kept a positive Sharpe Ratio "
        "out-of-sample with their in-sample-optimized parameters."
    )
    print(
        "If most tickers go negative or flip sign out-of-sample, the in-sample "
        "result was likely curve-fit rather than a real, tradable edge."
    )


if __name__ == "__main__":
    main()
