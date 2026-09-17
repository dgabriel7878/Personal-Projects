"""Runs every registered strategy across the configured ticker universe and
collects performance statistics for side-by-side comparison."""

from __future__ import annotations

import warnings
from typing import Iterable

import pandas as pd
from backtesting.lib import FractionalBacktest

from trading_bot.backtest.metrics import extract_summary
from trading_bot.config import (
    DAILY_INTERVAL,
    DAILY_PERIOD,
    DEFAULT_CASH,
    DEFAULT_COMMISSION,
    INTRADAY_INTERVAL,
    INTRADAY_PERIOD,
    UNIVERSE,
)
from trading_bot.data.loader import load_ohlcv
from trading_bot.strategies import STRATEGY_REGISTRY

warnings.filterwarnings("ignore")


def _period_interval(timeframe: str) -> tuple[str, str]:
    if timeframe == "daily":
        return DAILY_PERIOD, DAILY_INTERVAL
    if timeframe == "intraday":
        return INTRADAY_PERIOD, INTRADAY_INTERVAL
    raise ValueError(f"Unknown timeframe: {timeframe!r}")


def all_tickers(asset_classes: Iterable[str]) -> list[str]:
    tickers: list[str] = []
    for asset_class in asset_classes:
        tickers.extend(UNIVERSE[asset_class])
    return tickers


def run_all(
    asset_classes: Iterable[str] = tuple(UNIVERSE.keys()),
    timeframes: Iterable[str] = ("daily", "intraday"),
    cash: float = DEFAULT_CASH,
    commission: float = DEFAULT_COMMISSION,
) -> pd.DataFrame:
    """Backtest every strategy in STRATEGY_REGISTRY against every ticker in
    the requested asset classes, on whichever timeframe each strategy is
    registered for. Returns one row per (strategy, ticker) run; failures for
    an individual combo (e.g. missing data) are logged and skipped rather
    than aborting the whole comparison."""
    tickers = all_tickers(asset_classes)
    timeframes = set(timeframes)
    rows = []

    for name, strategy_cls, strategy_timeframe in STRATEGY_REGISTRY:
        if strategy_timeframe not in timeframes:
            continue
        period, interval = _period_interval(strategy_timeframe)

        for ticker in tickers:
            try:
                data = load_ohlcv(ticker, period, interval)
                if len(data) < 60:
                    raise ValueError(f"not enough bars ({len(data)}) to backtest")

                # FractionalBacktest (not plain Backtest) so high-priced
                # instruments like BTC-USD can still be sized correctly on a
                # modest cash balance -- Backtest only allows whole-unit
                # positions, which silently never trades anything priced
                # above the available cash.
                bt = FractionalBacktest(
                    data,
                    strategy_cls,
                    cash=cash,
                    commission=commission,
                    exclusive_orders=True,
                )
                stats = bt.run()
                rows.append(extract_summary(stats, name, ticker, strategy_timeframe))
            except Exception as exc:  # one bad ticker/strategy shouldn't sink the rest
                print(f"  [skip] {name} / {ticker} ({strategy_timeframe}): {exc}")

    return pd.DataFrame(rows)
