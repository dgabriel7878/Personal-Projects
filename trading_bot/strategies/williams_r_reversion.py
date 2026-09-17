"""Mean reversion via Williams %R: buy when the oscillator is deeply
oversold, exit once it recovers to overbought territory. Same underlying
idea as RSI mean reversion, but %R measures where price sits within its
recent high/low range rather than the size of recent moves."""

from backtesting import Strategy

from trading_bot.strategies.indicators import williams_r


class WilliamsRReversion(Strategy):
    n = 14
    oversold = -80
    overbought = -20

    def init(self):
        self.wr = self.I(williams_r, self.data.High, self.data.Low, self.data.Close, self.n)

    def next(self):
        if not self.position and self.wr[-1] < self.oversold:
            self.buy()
        elif self.position and self.wr[-1] > self.overbought:
            self.position.close()
