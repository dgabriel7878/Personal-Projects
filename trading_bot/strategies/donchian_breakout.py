"""Turtle-style trend-following breakout: buy an N-day high, exit an M-day low."""

from backtesting import Strategy

from trading_bot.strategies.indicators import donchian_channel


class DonchianBreakout(Strategy):
    entry_n = 20
    exit_n = 10

    def init(self):
        self.entry_upper, _ = self.I(
            donchian_channel, self.data.High, self.data.Low, self.entry_n
        )
        _, self.exit_lower = self.I(
            donchian_channel, self.data.High, self.data.Low, self.exit_n
        )

    def next(self):
        price = self.data.Close[-1]
        if not self.position and price >= self.entry_upper[-2]:
            self.buy()
        elif self.position and price <= self.exit_lower[-2]:
            self.position.close()
