from pandas import Series
from math import log10


class Signal:
    def __init__(self, arb_id: int, start_index: int, stop_index: int):
        self.arb_id:        int = arb_id
        self.start_index:   int = start_index
        self.stop_index:    int = stop_index
        self.time_series:   Series = None
        self.static:        bool = True
        self.shannon_index: float = 0
        self.plot_title:    str = ""
        self.j1979_title:   str = None
        self.j1979_pcc:     float = 0

    def normalize_and_set_metadata(self, normalize_strategy):
        self.set_shannon_index()
        self.update_static()
        self.set_plot_title()
        self.normalize(normalize_strategy)

    def set_shannon_index(self):
        si: float = 0.0
        n: int = self.time_series.__len__()
        for count in self.time_series.value_counts():
            # calculate proportion of this integer value in the total population of values
            p_i = count / n
            # calculate the Shannon Index (si) given p_i of this value.
            si += p_i * log10(p_i)
        si *= -1
        self.shannon_index = si

    def update_static(self):
        if self.shannon_index >= .000001:
            self.static = False

    def set_plot_title(self):
        self.plot_title = "Time Series from Bit Positions " + str(self.start_index) + " to " + str(self.stop_index) + \
                          " of Arb ID " + hex(int(self.arb_id))

    def normalize(self, normalize_strategy):
        normalize_strategy(self.time_series.values, copy=False)
