"""Walk-forward validation: optimize a strategy's parameters on an in-sample
(train) window, then run those exact parameters, unmodified, on a
held-out out-of-sample (test) window.

A strategy with a real edge should still show a positive Sharpe out of
sample, just smaller. One that only worked in-sample was curve-fit to that
particular history and should not be trusted with real money.
"""

from __future__ import annotations

import itertools
from types import SimpleNamespace
from typing import Iterable

import pandas as pd
from backtesting.lib import FractionalBacktest

from trading_bot.config import (
    DAILY_INTERVAL,
    DAILY_PERIOD,
    DEFAULT_CASH,
    DEFAULT_COMMISSION,
    INTRADAY_INTERVAL,
    INTRADAY_PERIOD,
)
from trading_bot.data.loader import load_ohlcv
from trading_bot.strategies import STRATEGY_REGISTRY
from trading_bot.strategies.bollinger_mean_reversion import BollingerMeanReversion
from trading_bot.strategies.donchian_breakout import DonchianBreakout
from trading_bot.strategies.macd_momentum import MacdMomentum
from trading_bot.strategies.opening_range_breakout import OpeningRangeBreakout
from trading_bot.strategies.rsi_mean_reversion import RsiMeanReversion
from trading_bot.strategies.sma_crossover import SmaCrossover

# Parameter grids searched in-sample, plus an optional constraint to reject
# nonsensical combinations (e.g. a "fast" average that isn't actually
# faster than the "slow" one).
PARAM_GRIDS = {
    SmaCrossover: dict(
        grid=dict(fast_n=range(10, 31, 5), slow_n=range(40, 101, 15)),
        constraint=lambda p: p.fast_n < p.slow_n,
    ),
    RsiMeanReversion: dict(
        grid=dict(oversold=range(20, 36, 5), exit_level=range(50, 66, 5)),
        constraint=lambda p: p.exit_level > p.oversold,
    ),
    BollingerMeanReversion: dict(
        grid=dict(n=range(15, 31, 5), n_std=[1.5, 2.0, 2.5]),
        constraint=None,
    ),
    MacdMomentum: dict(
        grid=dict(n_fast=[8, 12, 16], n_slow=[21, 26, 30], n_signal=[7, 9, 11]),
        constraint=lambda p: p.n_fast < p.n_slow,
    ),
    DonchianBreakout: dict(
        grid=dict(entry_n=range(10, 41, 10), exit_n=range(5, 21, 5)),
        constraint=lambda p: p.exit_n < p.entry_n,
    ),
    OpeningRangeBreakout: dict(
        grid=dict(range_minutes=[5, 15, 30, 60]),
        constraint=None,
    ),
}


def _period_interval(timeframe: str) -> tuple[str, str]:
    if timeframe == "daily":
        return DAILY_PERIOD, DAILY_INTERVAL
    if timeframe == "intraday":
        return INTRADAY_PERIOD, INTRADAY_INTERVAL
    raise ValueError(f"Unknown timeframe: {timeframe!r}")


def _strategy_lookup(strategy_name: str):
    for name, cls, timeframe in STRATEGY_REGISTRY:
        if name == strategy_name:
            return cls, timeframe
    raise ValueError(f"Unknown strategy: {strategy_name!r}")


def _split(data: pd.DataFrame, train_frac: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    cut = int(len(data) * train_frac)
    return data.iloc[:cut], data.iloc[cut:]


def _to_native(value):
    """Unwrap numpy scalar types (e.g. np.int64) picked up from range()/list
    grids so printed params read as plain Python numbers."""
    return value.item() if hasattr(value, "item") else value


def _grid_search(bt: FractionalBacktest, grid: dict, constraint) -> tuple[dict, pd.Series]:
    """Plain sequential grid search over `grid`, maximizing Sharpe Ratio.

    Avoids Backtest.optimize()'s built-in multiprocessing entirely -- our
    grids are small (a few dozen combinations at most), so a Python loop is
    plenty fast and sidesteps the (harmless, but very noisy) worker-process
    cleanup warnings that library triggers on some platforms.
    """
    keys = list(grid.keys())
    best_params, best_stats, best_sharpe = None, None, None

    for values in itertools.product(*(grid[k] for k in keys)):
        combo = dict(zip(keys, values))
        if constraint is not None and not constraint(SimpleNamespace(**combo)):
            continue

        stats = bt.run(**combo)
        sharpe = stats["Sharpe Ratio"]
        if pd.isna(sharpe):
            continue
        if best_sharpe is None or sharpe > best_sharpe:
            best_sharpe = sharpe
            best_params = {k: _to_native(v) for k, v in combo.items()}
            best_stats = stats

    if best_params is None:
        raise ValueError("no parameter combination produced any trades in-sample")
    return best_params, best_stats


def walk_forward(
    strategy_name: str,
    tickers: Iterable[str],
    train_frac: float = 0.7,
    cash: float = DEFAULT_CASH,
    commission: float = DEFAULT_COMMISSION,
) -> pd.DataFrame:
    strategy_cls, timeframe = _strategy_lookup(strategy_name)
    if strategy_cls not in PARAM_GRIDS:
        raise ValueError(f"No parameter grid registered for {strategy_name!r}")
    spec = PARAM_GRIDS[strategy_cls]
    period, interval = _period_interval(timeframe)

    rows = []
    for ticker in tickers:
        try:
            data = load_ohlcv(ticker, period, interval)
            train, test = _split(data, train_frac)
            if len(train) < 60 or len(test) < 30:
                raise ValueError("not enough bars for a train/test split")

            train_bt = FractionalBacktest(
                train, strategy_cls, cash=cash, commission=commission, exclusive_orders=True
            )
            best_params, train_stats = _grid_search(train_bt, spec["grid"], spec["constraint"])

            test_bt = FractionalBacktest(
                test, strategy_cls, cash=cash, commission=commission, exclusive_orders=True
            )
            test_stats = test_bt.run(**best_params)

            rows.append(
                {
                    "Ticker": ticker,
                    "Best Params": best_params,
                    "Train Sharpe": train_stats["Sharpe Ratio"],
                    "Train Return [%]": train_stats["Return [%]"],
                    "Test Sharpe": test_stats["Sharpe Ratio"],
                    "Test Return [%]": test_stats["Return [%]"],
                    "Test # Trades": test_stats["# Trades"],
                }
            )
        except Exception as exc:  # one bad ticker shouldn't sink the rest
            print(f"  [skip] {strategy_name} / {ticker}: {exc}")

    return pd.DataFrame(rows)
