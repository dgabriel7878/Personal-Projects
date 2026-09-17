"""Time-series (absolute) momentum: long whenever the trailing ~12-month
return is positive, flat otherwise. Popularized in dual-momentum /
tactical-allocation research (Antonacci, Faber) as a simple, low-turnover
way to avoid sustained drawdowns without trying to time tops and bottoms."""

from backtesting import Strategy

from trading_bot.strategies.indicators import momentum_return


class AbsoluteMomentum(Strategy):
    lookback = 252

    def init(self):
        self.momentum = self.I(momentum_return, self.data.Close, self.lookback)

    def next(self):
        if not self.position and self.momentum[-1] > 0:
            self.buy()
        elif self.position and self.momentum[-1] < 0:
            self.position.close()
