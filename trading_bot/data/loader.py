"""OHLCV data loading with on-disk caching, backed by yfinance.

Works uniformly for stocks/ETFs, futures continuous contracts, and crypto
pairs -- yfinance treats them all as regular tickers, the only difference
being the symbol convention (see trading_bot.config.UNIVERSE).
"""

from __future__ import annotations

import os

import pandas as pd
import yfinance as yf

from trading_bot.config import CACHE_DIR

REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


def _cache_path(ticker: str, period: str, interval: str) -> str:
    safe_ticker = ticker.replace("=", "_").replace("^", "")
    filename = f"{safe_ticker}_{period}_{interval}.csv"
    return os.path.join(CACHE_DIR, filename)


def load_ohlcv(
    ticker: str,
    period: str,
    interval: str,
    use_cache: bool = True,
) -> pd.DataFrame:
    """Return a clean OHLCV DataFrame for `ticker`, indexed by datetime.

    Raises ValueError if no data is available (bad ticker, delisted, or the
    requested interval/period combination isn't supported by the source).
    """
    cache_path = _cache_path(ticker, period, interval)

    if use_cache and os.path.exists(cache_path):
        return pd.read_csv(cache_path, index_col=0, parse_dates=True)

    df = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False,
        multi_level_index=False,
    )

    if df is None or df.empty:
        raise ValueError(
            f"No data returned for {ticker!r} (period={period!r}, interval={interval!r})"
        )

    df = df[REQUIRED_COLUMNS].dropna()
    df.index.name = "Date"

    if use_cache:
        os.makedirs(CACHE_DIR, exist_ok=True)
        df.to_csv(cache_path)

    return df
