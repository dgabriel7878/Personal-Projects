"""Shared position-sizing helper for strategies that want a hard stop-loss
sized to risk a fixed fraction of equity per trade, rather than betting
however much cash happens to be available."""


def risk_based_size(equity: float, price: float, stop_price: float, risk_per_trade: float):
    """Whole-unit position size such that if the stop is hit, the loss is
    approximately `risk_per_trade` fraction of current equity.

    Returns None if the stop distance isn't positive (shouldn't happen for
    a valid long stop, but guards against it) or rounds to zero units.
    """
    risk_per_unit = price - stop_price
    if risk_per_unit <= 0:
        return None
    size = round((equity * risk_per_trade) / risk_per_unit)
    return size if size >= 1 else None
