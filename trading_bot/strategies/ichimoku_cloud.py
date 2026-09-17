"""Ichimoku Cloud trend-following: buy when the Tenkan-sen crosses above
the Kijun-sen while price is above the cloud (confirming the uptrend),
exit when Tenkan crosses back below Kijun or price falls back into/below
the cloud."""

from backtesting import Strategy
from backtesting.lib import crossover

from trading_bot.strategies.indicators import ichimoku


class IchimokuCloud(Strategy):
    tenkan_n = 9
    kijun_n = 26
    senkou_b_n = 52

    def init(self):
        self.tenkan, self.kijun, self.span_a, self.span_b = self.I(
            ichimoku, self.data.High, self.data.Low, self.data.Close,
            self.tenkan_n, self.kijun_n, self.senkou_b_n,
        )

    def next(self):
        price = self.data.Close[-1]
        cloud_top = max(self.span_a[-1], self.span_b[-1])
        cloud_bottom = min(self.span_a[-1], self.span_b[-1])

        if not self.position:
            if crossover(self.tenkan, self.kijun) and price > cloud_top:
                self.buy()
        else:
            if crossover(self.kijun, self.tenkan) or price < cloud_bottom:
                self.position.close()
