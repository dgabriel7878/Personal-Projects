"""Trend-following regime filter: long only while three moving averages are
stacked in bullish order (fast > mid > slow), flat once that alignment
breaks. More conservative than a single crossover -- requires the whole
trend structure to agree, not just two lines touching."""

from backtesting import Strategy

from trading_bot.strategies.indicators import sma


class TripleMaAlignment(Strategy):
    fast_n = 10
    mid_n = 50
    slow_n = 200

    def init(self):
        self.fast = self.I(sma, self.data.Close, self.fast_n)
        self.mid = self.I(sma, self.data.Close, self.mid_n)
        self.slow = self.I(sma, self.data.Close, self.slow_n)

    def next(self):
        bullish = self.fast[-1] > self.mid[-1] > self.slow[-1]
        if not self.position and bullish:
            self.buy()
        elif self.position and not bullish:
            self.position.close()
