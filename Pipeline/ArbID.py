from typing import Callable, List
from pandas import DataFrame
from numpy import float64, logical_xor, mean, ndarray, sqrt, std, sum, uint8, zeros
from PipelineTimer import PipelineTimer


# noinspection PyArgumentList
class ArbID:
    def __init__(self, arb_id: int):
        self.id:                int = arb_id
        # These features are set by PreProcessing.py's generate_arb_id_dictionary
        self.dlc:               int = 0
        self.original_data:     DataFrame = None
        # These features are set in generate_binary_matrix_and_tang called by generate_arb_id_dictionary
        self.boolean_matrix:    ndarray = None
        self.tang:              ndarray = None
        self.static:            bool = True
        # These features are set in analyze_transmission_frequency called by generate_arb_id_dictionary
        self.ci_sensitivity:    float = 0.0
        self.freq_mean:         float = 0.0
        self.freq_std:          float = 0.0
        self.freq_ci:           tuple = None
        self.mean_to_ci_ratio:  float = 0.0
        self.synchronous:       bool = False
        # These features are set by LexicalAnalysis.py's get_composition
        self.tokenization:      List[tuple] = []
        self.padding:           List[int] = []

    def generate_binary_matrix_and_tang(self, a_timer: PipelineTimer, normalize_strategy: Callable):
        a_timer.start_nested_function_time()

        self.boolean_matrix = zeros((self.original_data.__len__(), self.dlc * 8), dtype=uint8)

        for i, row in enumerate(self.original_data.itertuples()):
            for j, cell in enumerate(row[1:]):
                # Skip cells that were already 0
                if cell > 0:
                    # i is the row in the boolean_matrix
                    # j*8 is the left hand bit for this byte in the payload
                    # j*8 + 8 is the right hand bit for this byte in the payload
                    # e.g. byte index 1 starts at bits 1*8 = 8 to 1*8+8 = 16; [8:16]
                    # likewise, byte index 7 starts at bits 7*8 = 56 to 7*8+8 = 64
                    # Numpy indexing is non-inclusive of the upper bound. So [0:8] is the first 7 elements
                    bin_string = format(cell, '08b')
                    self.boolean_matrix[i, j * 8:j * 8 + 8] = [x == '1' for x in bin_string]

        a_timer.set_hex_to_bool_matrix()

        if self.boolean_matrix.shape[0] > 1:
            a_timer.start_nested_function_time()

            transition_matrix = logical_xor(self.boolean_matrix[:-1, ], self.boolean_matrix[1:, ])
            self.tang = sum(transition_matrix, axis=0, dtype=float64)
            # Ensure there is no divide by zero issues
            if max(self.tang) > 0:
                normalize_strategy(self.tang, axis=0, copy=False)
                self.static = False

            a_timer.set_bool_matrix_to_tang()

    def analyze_transmission_frequency(self,
                                       time_convert:            int = 1000,
                                       ci_accuracy:             float = 1.645,
                                       synchronous_threshold:   float = 0.1):
        # Don't bother doing this if there isn't enough data. You would need to handle a bunch of edge cases anyways.
        if self.original_data.__len__() < 4:
            return

        self.ci_sensitivity = ci_accuracy
        # time_convert = 1000 is intended to convert seconds to milliseconds.
        freq_intervals = self.original_data.index[1:] - self.original_data.index[:-1]
        self.freq_mean = mean(freq_intervals) * time_convert
        self.freq_std = std(freq_intervals, ddof=1)*time_convert
        # Assumes distribution of freq_intervals is gaussian normal.
        mean_offset = ci_accuracy * self.freq_std / sqrt(len(freq_intervals))
        self.freq_ci = (self.freq_mean - mean_offset, self.freq_mean + mean_offset)
        # mean_to_ci_ratio is the ratio of the CI range to the mean value. This is to provide heuristic to determine
        # if this Arb ID can be called 'synchronous' given the time scale of its average transmission frequency.
        # For example, imagine an Arb ID transmitting with a mean frequency of exactly one second. Its 90% Confidence
        # Interval spans 50 milliseconds about that ideal mean. It's reasonable to assume this Arb ID was engineered to
        # be a 'synchronous' signal. However, a different Arb ID with a mean frequency of 40 milliseconds and the same
        # confidence interval could not be reasonably assumed to have been engineered to be 'synchronous'. This other
        # Arb ID was engineered to be 'high frequency' compared to the first example, but there isn't evidence that it's
        # intended to be a high frequency 'synchronous' process that adheres to a certain clock frequency.
        # This inference relies upon the assumption that the OEM didn't engineer the bus to be a train wreck with some
        # IDs losing an arbitrarily large percentage of their arbitration phases.
        self.mean_to_ci_ratio = 2*mean_offset/self.freq_mean
        if self.mean_to_ci_ratio <= synchronous_threshold:
            self.synchronous = True
