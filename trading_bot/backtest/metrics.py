"""Pull a clean, comparable row of stats out of a backtesting.py run."""

from __future__ import annotations

import pandas as pd


def extract_summary(stats: pd.Series, strategy: str, ticker: str, timeframe: str) -> dict:
    return {
        "Strategy": strategy,
        "Ticker": ticker,
        "Timeframe": timeframe,
        "Return [%]": stats.get("Return [%]"),
        "Buy & Hold Return [%]": stats.get("Buy & Hold Return [%]"),
        "Sharpe Ratio": stats.get("Sharpe Ratio"),
        "Sortino Ratio": stats.get("Sortino Ratio"),
        "Max. Drawdown [%]": stats.get("Max. Drawdown [%]"),
        "Win Rate [%]": stats.get("Win Rate [%]"),
        "# Trades": stats.get("# Trades"),
        "Profit Factor": stats.get("Profit Factor"),
        "SQN": stats.get("SQN"),
        "Exposure Time [%]": stats.get("Exposure Time [%]"),
    }
