"""Mean reversion via the Commodity Channel Index: buy when price is
unusually far below its recent average (relative to typical deviation),
exit once it swings to the opposite extreme."""

from backtesting import Strategy

from trading_bot.strategies.indicators import cci


class CciReversion(Strategy):
    n = 20
    oversold = -100
    overbought = 100

    def init(self):
        self.cci = self.I(cci, self.data.High, self.data.Low, self.data.Close, self.n)

    def next(self):
        if not self.position and self.cci[-1] < self.oversold:
            self.buy()
        elif self.position and self.cci[-1] > self.overbought:
            self.position.close()
