"""Volatility breakout: buy a close above the Keltner Channel's upper band
(EMA basis plus an ATR multiple), exit back at the basis line. Similar in
spirit to a Bollinger breakout, but ATR-based bands react to volatility
more smoothly than the standard-deviation bands do."""

from backtesting import Strategy

from trading_bot.strategies.indicators import keltner_channel


class KeltnerBreakout(Strategy):
    n = 20
    multiplier = 2.0

    def init(self):
        self.upper, self.middle, self.lower = self.I(
            keltner_channel, self.data.High, self.data.Low, self.data.Close, self.n, self.multiplier
        )

    def next(self):
        price = self.data.Close[-1]
        if not self.position and price > self.upper[-1]:
            self.buy()
        elif self.position and price < self.middle[-1]:
            self.position.close()
