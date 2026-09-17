"""Volatility breakout: buy a close above the Keltner Channel's upper band
(EMA basis plus an ATR multiple), exit back at the basis line. Similar in
spirit to a Bollinger breakout, but ATR-based bands react to volatility
more smoothly than the standard-deviation bands do.

Sized to risk a fixed fraction of equity per trade with a hard ATR-based
stop-loss, since the basis-line exit alone wouldn't protect against a
large adverse move happening before that exit triggers."""

from backtesting import Strategy

from trading_bot.strategies.indicators import atr, keltner_channel
from trading_bot.strategies.risk import risk_based_size


class KeltnerBreakout(Strategy):
    n = 20
    multiplier = 2.0
    risk_per_trade = 0.02
    sl_atr_mult = 2.0

    def init(self):
        self.upper, self.middle, self.lower = self.I(
            keltner_channel, self.data.High, self.data.Low, self.data.Close, self.n, self.multiplier
        )
        self.atr = self.I(atr, self.data.High, self.data.Low, self.data.Close, self.n)

    def next(self):
        price = self.data.Close[-1]
        if not self.position and price > self.upper[-1]:
            stop_price = price - self.sl_atr_mult * self.atr[-1]
            size = risk_based_size(self.equity, price, stop_price, self.risk_per_trade)
            if size:
                self.buy(size=size, sl=stop_price)
        elif self.position and price < self.middle[-1]:
            self.position.close()
