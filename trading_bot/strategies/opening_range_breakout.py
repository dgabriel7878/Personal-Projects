"""Intraday breakout strategy: define the day's opening range from its first
`range_minutes` of bars, buy a break above it, exit on a break below the
range low or at the last bar of the session (never holds overnight)."""

import pandas as pd
from backtesting import Strategy


class OpeningRangeBreakout(Strategy):
    range_minutes = 15

    def init(self):
        index = self.data.index
        high = pd.Series(self.data.High, index=index)
        low = pd.Series(self.data.Low, index=index)

        dates = index.date
        minutes_of_day = pd.Series(
            [t.hour * 60 + t.minute for t in index.time], index=index
        )
        session_open_minute = minutes_of_day.groupby(dates).transform("min")
        minutes_since_open = minutes_of_day - session_open_minute
        in_opening_window = minutes_since_open < self.range_minutes

        window_high = high.where(in_opening_window)
        window_low = low.where(in_opening_window)
        self.or_high = window_high.groupby(dates).transform("max").ffill().values
        self.or_low = window_low.groupby(dates).transform("min").ffill().values
        self.after_window = (~in_opening_window).values
        self.day_id = pd.factorize(dates)[0]

    def next(self):
        i = len(self.data) - 1
        if not self.after_window[i]:
            return

        is_last_bar_of_day = (
            i == len(self.day_id) - 1 or self.day_id[i + 1] != self.day_id[i]
        )
        price = self.data.Close[-1]

        if self.position:
            if is_last_bar_of_day or price <= self.or_low[i]:
                self.position.close()
            return

        if not is_last_bar_of_day and price >= self.or_high[i]:
            self.buy()
