"""ATR-based trend-following: stay long while the Supertrend line signals
an uptrend, flat when it flips to a downtrend. A popular alternative to
moving-average crossovers that adapts its stop distance to volatility.

Sized to risk a fixed fraction of equity per trade with a hard ATR-based
stop-loss -- the Supertrend line itself only exits at the next bar's close
after flipping, which wouldn't protect against a large adverse move
happening intrabar."""

from backtesting import Strategy

from trading_bot.strategies.indicators import atr, supertrend
from trading_bot.strategies.risk import risk_based_size


class SupertrendStrategy(Strategy):
    atr_n = 10
    multiplier = 3.0
    risk_per_trade = 0.02
    sl_atr_mult = 2.0

    def init(self):
        _, self.direction = self.I(
            supertrend, self.data.High, self.data.Low, self.data.Close, self.atr_n, self.multiplier
        )
        self.atr = self.I(atr, self.data.High, self.data.Low, self.data.Close, self.atr_n)

    def next(self):
        if not self.position and self.direction[-1] == 1:
            price = self.data.Close[-1]
            stop_price = price - self.sl_atr_mult * self.atr[-1]
            size = risk_based_size(self.equity, price, stop_price, self.risk_per_trade)
            if size:
                self.buy(size=size, sl=stop_price)
        elif self.position and self.direction[-1] == -1:
            self.position.close()
