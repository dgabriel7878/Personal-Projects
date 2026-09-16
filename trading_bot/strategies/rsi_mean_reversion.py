"""Mean-reversion swing strategy: buy oversold RSI, exit once it recovers."""

from backtesting import Strategy

from trading_bot.strategies.indicators import rsi


class RsiMeanReversion(Strategy):
    rsi_n = 14
    oversold = 30
    exit_level = 55

    def init(self):
        self.rsi = self.I(rsi, self.data.Close, self.rsi_n)

    def next(self):
        if not self.position and self.rsi[-1] < self.oversold:
            self.buy()
        elif self.position and self.rsi[-1] > self.exit_level:
            self.position.close()
