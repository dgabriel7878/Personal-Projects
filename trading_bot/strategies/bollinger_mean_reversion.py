"""Mean-reversion swing strategy using Bollinger Bands: buy the lower band,
exit at the middle band (the rolling mean)."""

from backtesting import Strategy

from trading_bot.strategies.indicators import bollinger_bands


class BollingerMeanReversion(Strategy):
    n = 20
    n_std = 2.0

    def init(self):
        self.upper, self.mid, self.lower = self.I(
            bollinger_bands, self.data.Close, self.n, self.n_std
        )

    def next(self):
        price = self.data.Close[-1]
        if not self.position and price < self.lower[-1]:
            self.buy()
        elif self.position and price > self.mid[-1]:
            self.position.close()
