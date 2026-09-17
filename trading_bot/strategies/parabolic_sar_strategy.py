"""Parabolic SAR trend-following: stay long while the SAR dots sit below
price (uptrend), flat once they flip above price. The SAR trails the
trend with an accelerating step, acting as a built-in trailing stop."""

from backtesting import Strategy

from trading_bot.strategies.indicators import parabolic_sar


class ParabolicSarStrategy(Strategy):
    af_step = 0.02
    af_max = 0.2

    def init(self):
        _, self.direction = self.I(
            parabolic_sar, self.data.High, self.data.Low, self.af_step, self.af_max
        )

    def next(self):
        if not self.position and self.direction[-1] == 1:
            self.buy()
        elif self.position and self.direction[-1] == -1:
            self.position.close()
