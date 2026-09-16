#!/usr/bin/env python3
"""Backtest every strategy in trading_bot.strategies across the configured
ticker universe and print a ranked comparison, so you can see which
strategy is actually worth taking to paper trading.

Examples:
    python scripts/run_backtests.py
    python scripts/run_backtests.py --asset-classes stocks crypto
    python scripts/run_backtests.py --timeframes daily
"""

import argparse
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from tabulate import tabulate

from trading_bot.backtest.runner import run_all
from trading_bot.config import DEFAULT_CASH, DEFAULT_COMMISSION, RESULTS_DIR, UNIVERSE

pd.set_option("display.width", 140)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--asset-classes",
        nargs="+",
        choices=list(UNIVERSE.keys()),
        default=list(UNIVERSE.keys()),
        help="Which asset classes to include (default: all).",
    )
    parser.add_argument(
        "--timeframes",
        nargs="+",
        choices=["daily", "intraday"],
        default=["daily", "intraday"],
        help="Which strategy timeframes to run (default: both).",
    )
    parser.add_argument("--cash", type=float, default=DEFAULT_CASH)
    parser.add_argument("--commission", type=float, default=DEFAULT_COMMISSION)
    return parser.parse_args()


def rank_strategies(results: pd.DataFrame) -> pd.DataFrame:
    return (
        results.groupby("Strategy")
        .agg(
            **{
                "Avg Sharpe": ("Sharpe Ratio", "mean"),
                "Avg Return [%]": ("Return [%]", "mean"),
                "Avg Max DD [%]": ("Max. Drawdown [%]", "mean"),
                "Avg Win Rate [%]": ("Win Rate [%]", "mean"),
                "Total Trades": ("# Trades", "sum"),
                "Markets Tested": ("Ticker", "count"),
            }
        )
        .sort_values("Avg Sharpe", ascending=False)
        .reset_index()
    )


def main():
    args = parse_args()

    print(
        f"Running backtests: asset_classes={args.asset_classes} "
        f"timeframes={args.timeframes} cash={args.cash} commission={args.commission}\n"
    )
    results = run_all(
        asset_classes=args.asset_classes,
        timeframes=args.timeframes,
        cash=args.cash,
        commission=args.commission,
    )

    if results.empty:
        print("No backtests produced results -- check data availability and try again.")
        return

    os.makedirs(RESULTS_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    detail_path = os.path.join(RESULTS_DIR, f"backtest_results_{timestamp}.csv")
    results.to_csv(detail_path, index=False)

    print("=== Per-run results ===")
    print(tabulate(results, headers="keys", tablefmt="github", showindex=False, floatfmt=".2f"))

    ranking = rank_strategies(results)
    ranking_path = os.path.join(RESULTS_DIR, f"strategy_ranking_{timestamp}.csv")
    ranking.to_csv(ranking_path, index=False)

    print("\n=== Strategy ranking (by average Sharpe Ratio across all markets tested) ===")
    print(tabulate(ranking, headers="keys", tablefmt="github", showindex=False, floatfmt=".2f"))

    print(f"\nDetailed results saved to: {detail_path}")
    print(f"Ranking saved to:          {ranking_path}")


if __name__ == "__main__":
    main()
