"""Larry Connors-style short-term mean reversion: only buy a sharp dip
(2-period RSI deeply oversold) while the underlying is in a longer-term
uptrend (price above its 200-day average). The trend filter is what
distinguishes this from a plain RSI mean-reversion strategy -- it only
fades dips, never tries to catch a falling knife in a downtrend."""

from backtesting import Strategy

from trading_bot.strategies.indicators import rsi, sma


class Rsi2MeanReversion(Strategy):
    rsi_n = 2
    trend_n = 200
    entry_threshold = 10
    exit_threshold = 70

    def init(self):
        self.rsi2 = self.I(rsi, self.data.Close, self.rsi_n)
        self.trend_sma = self.I(sma, self.data.Close, self.trend_n)

    def next(self):
        price = self.data.Close[-1]
        if not self.position:
            if self.rsi2[-1] < self.entry_threshold and price > self.trend_sma[-1]:
                self.buy()
        elif self.rsi2[-1] > self.exit_threshold:
            self.position.close()
