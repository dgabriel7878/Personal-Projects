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
from trading_bot.strategies.absolute_momentum import AbsoluteMomentum
from trading_bot.strategies.accum_dist_trend import AccumDistTrend
from trading_bot.strategies.adx_dmi_trend import AdxDmiTrend
from trading_bot.strategies.awesome_oscillator_strategy import AwesomeOscillatorStrategy
from trading_bot.strategies.bollinger_mean_reversion import BollingerMeanReversion
from trading_bot.strategies.bollinger_squeeze_breakout import BollingerSqueezeBreakout
from trading_bot.strategies.cci_reversion import CciReversion
from trading_bot.strategies.chaikin_money_flow_strategy import ChaikinMoneyFlowStrategy
from trading_bot.strategies.donchian_breakout import DonchianBreakout
from trading_bot.strategies.ema_crossover import EmaCrossover
from trading_bot.strategies.fisher_transform_strategy import FisherTransformStrategy
from trading_bot.strategies.ichimoku_cloud import IchimokuCloud
from trading_bot.strategies.intraday_rsi_reversion import IntradayRsiReversion
from trading_bot.strategies.keltner_breakout import KeltnerBreakout
from trading_bot.strategies.linreg_trend import LinregTrend
from trading_bot.strategies.macd_momentum import MacdMomentum
from trading_bot.strategies.money_flow_index_reversion import MoneyFlowIndexReversion
from trading_bot.strategies.obv_trend import ObvTrend
from trading_bot.strategies.opening_range_breakout import OpeningRangeBreakout
from trading_bot.strategies.parabolic_sar_strategy import ParabolicSarStrategy
from trading_bot.strategies.return_zscore_reversal import ReturnZscoreReversal
from trading_bot.strategies.roc_momentum import RocMomentum
from trading_bot.strategies.rsi2_connors import Rsi2MeanReversion
from trading_bot.strategies.rsi_mean_reversion import RsiMeanReversion
from trading_bot.strategies.sma200_trend_filter import Sma200TrendFilter
from trading_bot.strategies.sma_crossover import SmaCrossover
from trading_bot.strategies.stochastic_oscillator import StochasticOscillator
from trading_bot.strategies.supertrend_strategy import SupertrendStrategy
from trading_bot.strategies.triple_ma_alignment import TripleMaAlignment
from trading_bot.strategies.turn_of_month import TurnOfMonth
from trading_bot.strategies.turtle_soup import TurtleSoup
from trading_bot.strategies.vortex_trend import VortexTrend
from trading_bot.strategies.vwap_mean_reversion import VwapMeanReversion
from trading_bot.strategies.williams_r_reversion import WilliamsRReversion

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
    Sma200TrendFilter: dict(
        grid=dict(sma_n=range(100, 251, 50)),
        constraint=None,
    ),
    Rsi2MeanReversion: dict(
        grid=dict(
            entry_threshold=[5, 10, 15],
            exit_threshold=[60, 70, 80],
            trend_n=[150, 200, 250],
        ),
        constraint=lambda p: p.exit_threshold > p.entry_threshold,
    ),
    SupertrendStrategy: dict(
        grid=dict(atr_n=[7, 10, 14], multiplier=[2.0, 3.0, 4.0]),
        constraint=None,
    ),
    StochasticOscillator: dict(
        grid=dict(k_period=[9, 14, 21], oversold=[15, 20, 25], overbought=[75, 80, 85]),
        constraint=lambda p: p.overbought > p.oversold,
    ),
    EmaCrossover: dict(
        grid=dict(fast_n=range(8, 21, 4), slow_n=range(20, 61, 10)),
        constraint=lambda p: p.fast_n < p.slow_n,
    ),
    TripleMaAlignment: dict(
        grid=dict(fast_n=[5, 10, 15], mid_n=[30, 50, 70], slow_n=[150, 200, 250]),
        constraint=lambda p: p.fast_n < p.mid_n < p.slow_n,
    ),
    AdxDmiTrend: dict(
        grid=dict(n=[10, 14, 20], adx_threshold=[15, 20, 25, 30]),
        constraint=None,
    ),
    IchimokuCloud: dict(
        grid=dict(tenkan_n=[7, 9, 12], kijun_n=[22, 26, 30]),
        constraint=lambda p: p.tenkan_n < p.kijun_n,
    ),
    ParabolicSarStrategy: dict(
        grid=dict(af_step=[0.01, 0.02, 0.03], af_max=[0.1, 0.2, 0.3]),
        constraint=None,
    ),
    KeltnerBreakout: dict(
        grid=dict(n=[14, 20, 26], multiplier=[1.5, 2.0, 2.5]),
        constraint=None,
    ),
    LinregTrend: dict(
        grid=dict(n=[10, 20, 30, 50]),
        constraint=None,
    ),
    RocMomentum: dict(
        grid=dict(n=[10, 20, 30, 50]),
        constraint=None,
    ),
    AbsoluteMomentum: dict(
        grid=dict(lookback=[126, 189, 252]),
        constraint=None,
    ),
    WilliamsRReversion: dict(
        grid=dict(n=[10, 14, 21], oversold=[-90, -80, -70], overbought=[-30, -20, -10]),
        constraint=lambda p: p.overbought > p.oversold,
    ),
    CciReversion: dict(
        grid=dict(n=[14, 20, 30], oversold=[-150, -100, -50], overbought=[50, 100, 150]),
        constraint=lambda p: p.overbought > p.oversold,
    ),
    ReturnZscoreReversal: dict(
        grid=dict(n=[10, 20, 30], entry_z=[-2.5, -2.0, -1.5]),
        constraint=None,
    ),
    TurtleSoup: dict(
        grid=dict(n=[10, 20, 30], hold_bars=[3, 5, 10]),
        constraint=None,
    ),
    BollingerSqueezeBreakout: dict(
        grid=dict(n=[15, 20, 25], squeeze_percentile=[0.1, 0.2, 0.3]),
        constraint=None,
    ),
    ObvTrend: dict(
        grid=dict(signal_n=[10, 20, 30]),
        constraint=None,
    ),
    ChaikinMoneyFlowStrategy: dict(
        grid=dict(n=[10, 20, 30]),
        constraint=None,
    ),
    AccumDistTrend: dict(
        grid=dict(signal_n=[10, 20, 30]),
        constraint=None,
    ),
    TurnOfMonth: dict(
        grid=dict(first_n_days=[1, 3, 5], last_n_days=[1, 3, 5]),
        constraint=None,
    ),
    AwesomeOscillatorStrategy: dict(
        grid=dict(n_fast=[3, 5, 8], n_slow=[21, 34, 50]),
        constraint=lambda p: p.n_fast < p.n_slow,
    ),
    FisherTransformStrategy: dict(
        grid=dict(n=[6, 10, 14, 20]),
        constraint=None,
    ),
    MoneyFlowIndexReversion: dict(
        grid=dict(n=[10, 14, 21], oversold=[10, 20, 30], overbought=[70, 80, 90]),
        constraint=lambda p: p.overbought > p.oversold,
    ),
    VortexTrend: dict(
        grid=dict(n=[10, 14, 21, 28]),
        constraint=None,
    ),
    VwapMeanReversion: dict(
        grid=dict(entry_atr_mult=[1.0, 1.5, 2.0], stop_atr_mult=[0.5, 1.0, 1.5]),
        constraint=None,
    ),
    IntradayRsiReversion: dict(
        grid=dict(oversold=[20, 25, 30], overbought=[70, 75, 80]),
        constraint=lambda p: p.overbought > p.oversold,
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
