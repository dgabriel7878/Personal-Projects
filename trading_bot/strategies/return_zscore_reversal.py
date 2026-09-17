"""Short-term shock reversal: buy after an unusually large single-day drop
relative to recent volatility (a return z-score deep in negative
territory), exit once returns normalize. Reacts to sudden moves rather
than a price level's distance from its average."""

from backtesting import Strategy

from trading_bot.strategies.indicators import return_zscore


class ReturnZscoreReversal(Strategy):
    n = 20
    entry_z = -2.0
    exit_z = 0.0

    def init(self):
        self.zscore = self.I(return_zscore, self.data.Close, self.n)

    def next(self):
        if not self.position and self.zscore[-1] < self.entry_z:
            self.buy()
        elif self.position and self.zscore[-1] > self.exit_z:
            self.position.close()
