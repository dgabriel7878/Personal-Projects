"""Shared position-sizing helper for strategies that want a hard stop-loss
sized to risk a fixed fraction of equity per trade, rather than betting
however much cash happens to be available."""


def risk_based_size(
    equity: float,
    price: float,
    stop_price: float,
    risk_per_trade: float,
    max_leverage: float = 1.0,
):
    """Whole-unit position size such that if the stop is hit, the loss is
    approximately `risk_per_trade` fraction of current equity.

    Works for both a long stop (stop_price below price) and a short stop
    (stop_price above price) -- the risk distance is just the absolute
    gap between entry and stop, direction doesn't matter for sizing.

    Capped so the position's notional value never exceeds `max_leverage`
    times equity (1.0 = no leverage, fully-invested cap). Without this, a
    stop set tight relative to price -- routine on fast intraday bars,
    where a 1x-ATR stop might be a few tenths of a percent away -- makes
    the pure risk/distance formula demand an account can't actually
    afford (a 0.2%-away stop needs 10x leverage to risk 2% of equity on
    a $10k account), and the order would simply never fill.

    Returns None if price and stop_price are equal (zero risk distance,
    shouldn't happen for a valid stop) or the computed size rounds to
    zero units.
    """
    risk_per_unit = abs(price - stop_price)
    if risk_per_unit <= 0:
        return None
    size = (equity * risk_per_trade) / risk_per_unit
    max_affordable = (equity * max_leverage) / price
    size = round(min(size, max_affordable))
    return size if size >= 1 else None
