#!/usr/bin/env python3
"""Prints today's ranked watchlist: the most active/newsworthy stocks
right now, via trading_bot.scanner.news_scanner. A selection tool, not a
strategy -- see that module's docstring before wiring its output into any
live trading.

Requires ALPACA_API_KEY and ALPACA_SECRET_KEY in the environment -- copy
.env.example to .env and fill in your Alpaca paper trading keys.

Usage:
    python scripts/scan_movers.py [--top N] [--pool N] [--news-hours N]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from trading_bot.scanner.news_scanner import rank_candidates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top", type=int, default=15, help="Symbols to print (default: 15)")
    parser.add_argument("--pool", type=int, default=40, help="Candidate pool size before ranking (default: 40)")
    parser.add_argument("--news-hours", type=int, default=18, help="News lookback window in hours (default: 18)")
    args = parser.parse_args()

    if "ALPACA_API_KEY" not in os.environ or "ALPACA_SECRET_KEY" not in os.environ:
        print(
            "Missing ALPACA_API_KEY / ALPACA_SECRET_KEY.\n"
            "Copy .env.example to .env and fill in your paper trading keys from "
            "https://app.alpaca.markets/paper/dashboard/overview"
        )
        sys.exit(1)

    ranked = rank_candidates(top_n=args.top, active_pool=args.pool, news_lookback_hours=args.news_hours)

    print(f"=== Today's watchlist (top {len(ranked)}, ranked by catalyst > |% move| > volume) ===\n")
    header = f"{'Symbol':8s} {'Catalyst':9s} {'News #':7s} {'% Chg':8s} {'Volume':>14s} {'Trades':>10s}"
    print(header)
    print("-" * len(header))
    for r in ranked:
        pct = f"{r['percent_change']:+.2f}%" if r["percent_change"] is not None else "n/a"
        vol = f"{r['volume']:,.0f}" if r["volume"] is not None else "n/a"
        trades = f"{r['trade_count']:,.0f}" if r["trade_count"] is not None else "n/a"
        print(f"{r['symbol']:8s} {'yes' if r['has_catalyst'] else 'no':9s} {r['news_count']:<7d} {pct:8s} {vol:>14s} {trades:>10s}")


if __name__ == "__main__":
    main()
