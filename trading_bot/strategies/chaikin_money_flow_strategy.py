"""Volume-weighted trend confirmation: buy when Chaikin Money Flow crosses
above zero (buying pressure, weighted by where each bar closes within its
range, outweighs selling pressure), exit on the reverse cross."""

from backtesting import Strategy

from trading_bot.strategies.indicators import chaikin_money_flow


class ChaikinMoneyFlowStrategy(Strategy):
    n = 20

    def init(self):
        self.cmf = self.I(
            chaikin_money_flow, self.data.High, self.data.Low, self.data.Close, self.data.Volume, self.n
        )

    def next(self):
        if not self.position and self.cmf[-1] > 0 and self.cmf[-2] <= 0:
            self.buy()
        elif self.position and self.cmf[-1] < 0 and self.cmf[-2] >= 0:
            self.position.close()
