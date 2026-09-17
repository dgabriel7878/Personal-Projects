"""Mean reversion via the Money Flow Index: an RSI analog that weights
gains/losses by dollar volume rather than price change alone. Buy deeply
oversold, exit once it recovers to overbought."""

from backtesting import Strategy

from trading_bot.strategies.indicators import money_flow_index


class MoneyFlowIndexReversion(Strategy):
    n = 14
    oversold = 20
    overbought = 80

    def init(self):
        self.mfi = self.I(
            money_flow_index, self.data.High, self.data.Low, self.data.Close, self.data.Volume, self.n
        )

    def next(self):
        if not self.position and self.mfi[-1] < self.oversold:
            self.buy()
        elif self.position and self.mfi[-1] > self.overbought:
            self.position.close()
