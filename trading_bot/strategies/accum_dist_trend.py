"""Volume-confirmed trend following via the Accumulation/Distribution Line:
buy when the A/D line crosses above its own moving average, exit on the
reverse cross. Weights each bar's volume by where the close falls in its
high/low range, distinct from OBV's simpler up/down-day volume split."""

from backtesting import Strategy
from backtesting.lib import crossover

from trading_bot.strategies.indicators import accum_dist, sma


class AccumDistTrend(Strategy):
    signal_n = 20

    def init(self):
        self.ad_line = self.I(accum_dist, self.data.High, self.data.Low, self.data.Close, self.data.Volume)
        self.ad_signal = self.I(sma, self.ad_line, self.signal_n)

    def next(self):
        if crossover(self.ad_line, self.ad_signal):
            self.position.close()
            self.buy()
        elif crossover(self.ad_signal, self.ad_line):
            self.position.close()
