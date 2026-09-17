"""Daily paper-trading execution against Alpaca.

Computes the same Supertrend signal used in backtesting from the latest
daily bars, then reconciles the live position against it: opens a
risk-sized position with a hard ATR stop-loss when the signal turns
long, closes it when the signal flips down, does nothing otherwise.

Meant to run once per trading day (e.g. after market close, or before the
next open) -- Supertrend is a daily-bar strategy, not an intraday one, so
there's no need for a continuously-running process. Scoped to US
stocks/ETFs, which is what Alpaca's standard equities API supports
cleanly (whole-share orders, bracket stop-losses); crypto and futures
would need different order handling and aren't covered here.

Requires ALPACA_API_KEY and ALPACA_SECRET_KEY in the environment (see
.env.example) from a free Alpaca **paper trading** account -- never put
live-account keys here.
"""

from __future__ import annotations

import os

from alpaca.common.exceptions import APIError
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderClass, OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest, StopLossRequest

from trading_bot.data.loader import load_ohlcv
from trading_bot.strategies.indicators import atr, supertrend
from trading_bot.strategies.risk import risk_based_size

# Mirrors trading_bot.strategies.supertrend_strategy.SupertrendStrategy's
# defaults, so the live signal matches what was backtested.
ATR_N = 10
MULTIPLIER = 3.0
SL_ATR_MULT = 2.0
RISK_PER_TRADE = 0.02


def get_client() -> TradingClient:
    api_key = os.environ["ALPACA_API_KEY"]
    secret_key = os.environ["ALPACA_SECRET_KEY"]
    return TradingClient(api_key, secret_key, paper=True)


def current_qty(client: TradingClient, symbol: str) -> float:
    """Returns 0.0 if there's genuinely no open position for `symbol` (a
    404 from Alpaca). Anything else -- auth failures, rate limits, a
    typo'd symbol -- is a real problem and must not be silently treated
    as "no position", so it's re-raised."""
    try:
        position = client.get_open_position(symbol)
        return float(position.qty)
    except APIError as exc:
        if exc.status_code == 404:
            return 0.0
        raise


def compute_signal(symbol: str, atr_n: int = ATR_N, multiplier: float = MULTIPLIER):
    """Returns (direction, latest_close, latest_atr).

    Pulls ~1 year of daily bars (fresh, not cached) so the Supertrend/ATR
    warmup period is well behind the most recent bar.
    """
    data = load_ohlcv(symbol, period="1y", interval="1d", use_cache=False)
    _, direction = supertrend(data.High, data.Low, data.Close, atr_n, multiplier)
    atr_series = atr(data.High, data.Low, data.Close, atr_n)
    return int(direction.iloc[-1]), float(data.Close.iloc[-1]), float(atr_series.iloc[-1])


def reconcile(
    symbol: str,
    atr_n: int = ATR_N,
    multiplier: float = MULTIPLIER,
    sl_atr_mult: float = SL_ATR_MULT,
    risk_per_trade: float = RISK_PER_TRADE,
    dry_run: bool = False,
    client: TradingClient | None = None,
) -> str:
    """Compare the desired position (from today's Supertrend signal) to
    the live position and place whatever single order is needed to
    reconcile them. Returns a short human-readable summary."""
    client = client or get_client()
    direction, price, atr_value = compute_signal(symbol, atr_n, multiplier)
    qty_held = current_qty(client, symbol)

    if direction == 1 and qty_held == 0:
        stop_price = round(price - sl_atr_mult * atr_value, 2)
        account = client.get_account()
        qty = risk_based_size(float(account.equity), price, stop_price, risk_per_trade)

        if not qty or qty < 1:
            return f"{symbol}: signal is LONG but risk-based size < 1 share -- skipping"
        if dry_run:
            return f"{symbol}: [dry-run] would BUY {qty} shares @ ~{price:.2f}, stop-loss @ {stop_price:.2f}"

        order = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            # OTO (One-Triggers-Other), not BRACKET: we only want a
            # contingent stop-loss leg, no take-profit -- exits are driven
            # by the next day's signal flip, not a fixed profit target.
            # BRACKET requires both legs and would reject this order.
            order_class=OrderClass.OTO,
            stop_loss=StopLossRequest(stop_price=stop_price),
        )
        client.submit_order(order)
        return f"{symbol}: BUY {qty} shares @ ~{price:.2f}, stop-loss @ {stop_price:.2f}"

    if direction == -1 and qty_held > 0:
        if dry_run:
            return f"{symbol}: [dry-run] would CLOSE existing {qty_held:g}-share position"
        client.close_position(symbol)
        return f"{symbol}: CLOSE existing {qty_held:g}-share position (trend flipped down)"

    return (
        f"{symbol}: no action (signal={'long' if direction == 1 else 'flat'}, "
        f"current position={qty_held:g} shares)"
    )
