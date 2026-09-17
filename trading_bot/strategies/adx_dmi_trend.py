"""Trend-following with a strength filter: buy when +DI crosses above -DI
(bullish direction) but only when ADX confirms the trend has real strength,
exit when -DI crosses back above +DI. Avoids trading directional crosses
during a weak, choppy market."""

from backtesting import Strategy
from backtesting.lib import crossover

from trading_bot.strategies.indicators import adx_dmi


class AdxDmiTrend(Strategy):
    n = 14
    adx_threshold = 20

    def init(self):
        self.plus_di, self.minus_di, self.adx = self.I(
            adx_dmi, self.data.High, self.data.Low, self.data.Close, self.n
        )

    def next(self):
        if not self.position:
            if crossover(self.plus_di, self.minus_di) and self.adx[-1] > self.adx_threshold:
                self.buy()
        elif crossover(self.minus_di, self.plus_di):
            self.position.close()
