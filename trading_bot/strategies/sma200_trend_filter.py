"""Long-only regime filter: hold whenever price is above its 200-day
average, flat otherwise. Popularized by Mebane Faber's "A Quantitative
Approach to Tactical Asset Allocation" -- about as simple and widely
replicated a trend rule as exists."""

from backtesting import Strategy

from trading_bot.strategies.indicators import sma


class Sma200TrendFilter(Strategy):
    sma_n = 200

    def init(self):
        self.trend_sma = self.I(sma, self.data.Close, self.sma_n)

    def next(self):
        price = self.data.Close[-1]
        if not self.position and price > self.trend_sma[-1]:
            self.buy()
        elif self.position and price < self.trend_sma[-1]:
            self.position.close()
