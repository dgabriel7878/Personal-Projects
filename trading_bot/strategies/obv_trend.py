"""Volume-confirmed trend following: buy when On-Balance Volume crosses
above its own moving average (volume flow turning bullish), exit on the
reverse cross. Treats sustained volume pressure as the primary signal
rather than price alone."""

from backtesting import Strategy
from backtesting.lib import crossover

from trading_bot.strategies.indicators import obv, sma


class ObvTrend(Strategy):
    signal_n = 20

    def init(self):
        self.obv = self.I(obv, self.data.Close, self.data.Volume)
        self.obv_signal = self.I(sma, self.obv, self.signal_n)

    def next(self):
        if crossover(self.obv, self.obv_signal):
            self.position.close()
            self.buy()
        elif crossover(self.obv_signal, self.obv):
            self.position.close()
