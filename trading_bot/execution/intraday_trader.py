"""Intraday paper-trading execution against Alpaca: bidirectional
(long/short), checked repeatedly during market hours rather than once a
day. Mirrors the exact entry/exit logic of VwapMeanReversion and
IntradayRsiReversion (trading_bot/strategies/) so the live signal matches
what was backtested.

Meant to be invoked every few minutes during market hours (see README),
not run once daily like the Supertrend module -- these are same-day
strategies that flatten before the close, never holding overnight.

Requires ALPACA_API_KEY and ALPACA_SECRET_KEY in the environment (see
.env.example) from a free Alpaca **paper trading** account.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from alpaca.common.exceptions import APIError
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderClass, OrderSide, PositionSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest, StopLossRequest

from trading_bot.data.loader import load_ohlcv
from trading_bot.strategies.indicators import atr, rsi, session_vwap
from trading_bot.strategies.risk import risk_based_size

RISK_PER_TRADE = 0.02
MARKET_CLOSE_HOUR_ET = 16
FLATTEN_BUFFER_MINUTES = 10  # stop opening new trades / start flattening this many minutes before the close


def get_client() -> TradingClient:
    api_key = os.environ["ALPACA_API_KEY"]
    secret_key = os.environ["ALPACA_SECRET_KEY"]
    return TradingClient(api_key, secret_key, paper=True)


def is_near_market_close(buffer_minutes: int = FLATTEN_BUFFER_MINUTES) -> bool:
    """True within `buffer_minutes` of the 4:00pm ET close, by wall-clock
    time. This is calendar knowledge, not a peek at future price bars --
    a real trader also knows what time the market closes."""
    now_et = datetime.now(ZoneInfo("America/New_York"))
    close_time = now_et.replace(hour=MARKET_CLOSE_HOUR_ET, minute=0, second=0, microsecond=0)
    return now_et >= close_time - timedelta(minutes=buffer_minutes)


def current_side(client: TradingClient, symbol: str):
    """Returns ('long' | 'short' | None, qty_held)."""
    try:
        position = client.get_open_position(symbol)
        side = "short" if position.side == PositionSide.SHORT else "long"
        return side, abs(float(position.qty))
    except APIError as exc:
        if exc.status_code == 404:
            return None, 0.0
        raise


def vwap_decision(
    data: pd.DataFrame,
    side: str | None,
    is_near_close: bool,
    atr_n: int = 14,
    entry_atr_mult: float = 1.5,
    stop_atr_mult: float = 1.0,
):
    """Mirrors VwapMeanReversion.next(). Returns (action, stop_price)
    where action is 'enter_long' / 'enter_short' / 'exit' / None."""
    vwap = session_vwap(data.High, data.Low, data.Close, data.Volume, data.index)
    atr_series = atr(data.High, data.Low, data.Close, atr_n)
    price = float(data.Close.iloc[-1])
    vwap_now, atr_now = vwap.iloc[-1], atr_series.iloc[-1]

    if side is not None:
        if is_near_close:
            return "exit", None
        if side == "long" and price >= vwap_now:
            return "exit", None
        if side == "short" and price <= vwap_now:
            return "exit", None
        return None, None

    if is_near_close or not atr_now or np.isnan(atr_now):
        return None, None

    deviation = price - vwap_now
    if deviation < -entry_atr_mult * atr_now:
        return "enter_long", price - stop_atr_mult * atr_now
    if deviation > entry_atr_mult * atr_now:
        return "enter_short", price + stop_atr_mult * atr_now
    return None, None


def rsi_decision(
    data: pd.DataFrame,
    side: str | None,
    is_near_close: bool,
    rsi_n: int = 14,
    oversold: float = 30,
    overbought: float = 70,
    atr_n: int = 14,
    stop_atr_mult: float = 1.0,
):
    """Mirrors IntradayRsiReversion.next()."""
    rsi_series = rsi(data.Close, rsi_n)
    atr_series = atr(data.High, data.Low, data.Close, atr_n)
    price = float(data.Close.iloc[-1])
    rsi_now, atr_now = rsi_series.iloc[-1], atr_series.iloc[-1]

    if side is not None:
        if is_near_close:
            return "exit", None
        if side == "long" and rsi_now >= 50:
            return "exit", None
        if side == "short" and rsi_now <= 50:
            return "exit", None
        return None, None

    if is_near_close or not atr_now or np.isnan(atr_now):
        return None, None

    if rsi_now < oversold:
        return "enter_long", price - stop_atr_mult * atr_now
    if rsi_now > overbought:
        return "enter_short", price + stop_atr_mult * atr_now
    return None, None


DECISION_FUNCS = {"vwap": vwap_decision, "rsi": rsi_decision}


def reconcile(
    symbol: str,
    strategy: str = "vwap",
    risk_per_trade: float = RISK_PER_TRADE,
    dry_run: bool = False,
    client: TradingClient | None = None,
    **strategy_kwargs,
) -> str:
    if strategy not in DECISION_FUNCS:
        raise ValueError(f"Unknown strategy {strategy!r}, expected one of {list(DECISION_FUNCS)}")

    client = client or get_client()
    # 5 days of 5-min bars: enough for ATR/RSI warmup across the VWAP's
    # own daily resets, without pulling in stale history that's irrelevant
    # to right now.
    data = load_ohlcv(symbol, period="5d", interval="5m", use_cache=False)
    side, qty_held = current_side(client, symbol)
    near_close = is_near_market_close()

    action, stop_price = DECISION_FUNCS[strategy](data, side, near_close, **strategy_kwargs)
    price = float(data.Close.iloc[-1])

    if action == "exit":
        verb = "SELL to close long" if side == "long" else "BUY to cover short"
        if dry_run:
            return f"{symbol}: [dry-run] would {verb} {qty_held:g} shares"
        client.close_position(symbol)
        return f"{symbol}: {verb} {qty_held:g} shares"

    if action in ("enter_long", "enter_short"):
        account = client.get_account()
        size = risk_based_size(float(account.equity), price, stop_price, risk_per_trade)
        if not size:
            return f"{symbol}: {action} signal but risk-based size < 1 share -- skipping"

        order_side = OrderSide.BUY if action == "enter_long" else OrderSide.SELL
        label = "BUY" if action == "enter_long" else "SELL SHORT"
        stop_price = round(stop_price, 2)
        if dry_run:
            return f"{symbol}: [dry-run] would {label} {size} shares @ ~{price:.2f}, stop-loss @ {stop_price:.2f}"

        order = MarketOrderRequest(
            symbol=symbol,
            qty=size,
            side=order_side,
            time_in_force=TimeInForce.DAY,
            order_class=OrderClass.OTO,
            stop_loss=StopLossRequest(stop_price=stop_price),
        )
        client.submit_order(order)
        return f"{symbol}: {label} {size} shares @ ~{price:.2f}, stop-loss @ {stop_price:.2f}"

    return f"{symbol}: no action (side={side or 'flat'}, near_close={near_close})"
