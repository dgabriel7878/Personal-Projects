"""Contrarian fade of a failed Donchian breakdown ("Turtle Soup"): when
price breaks below the N-day low but closes back above it the same bar,
that's read as a trapped-seller false breakdown, so buy the reclaim. Exits
after a fixed holding period rather than waiting for a new trend signal."""

from backtesting import Strategy

from trading_bot.strategies.indicators import donchian_channel


class TurtleSoup(Strategy):
    n = 20
    hold_bars = 5

    def init(self):
        _, self.channel_lower = self.I(donchian_channel, self.data.High, self.data.Low, self.n)
        self.entry_bar = None

    def next(self):
        i = len(self.data) - 1
        if not self.position:
            if (
                i >= 1
                and self.data.Low[-1] < self.channel_lower[-2]
                and self.data.Close[-1] > self.channel_lower[-2]
            ):
                self.buy()
                self.entry_bar = i
        elif i - self.entry_bar >= self.hold_bars:
            self.position.close()
