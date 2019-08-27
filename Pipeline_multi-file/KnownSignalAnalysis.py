from numpy import float64, nditer, uint64, zeros, ndarray, inf
from pandas import Series, DataFrame
from os import path, remove
from pickle import load
from ArbID import ArbID
from Signal import Signal
from PipelineTimer import PipelineTimer
from typing import List
from scipy import integrate


def transform_signal(a_timer: PipelineTimer,
                     arb_id_dict: dict,
                     signal_dict: dict,
                     transform_pickle_filename: str,
                     normalize_strategy,
                     given_arb_id: int,
                     force=False):
    if force and path.isfile(transform_pickle_filename):
        remove(transform_pickle_filename)
    if path.isfile(transform_pickle_filename):
            print("\nSignal transformation already completed and forcing is turned off. Using pickled data...")
            return load(open(transform_pickle_filename, "rb"))

    a_timer.start_function_time()

    transform_dict = signal_dict

    # arb_id_dict[given_arb_id * 256] = ArbID(given_arb_id * 256)

    for k, arb_id in arb_id_dict.items():
        # print(str(arb_id.id) + " == " + str(given_arb_id) + " ?\n")
        if arb_id.id == given_arb_id:
            arb_id.static = False
            arb_id.short = False
            if not arb_id.static:
                for token in arb_id.tokenization:
                    a_timer.start_iteration_time()

                    signal = Signal(k * 256, token[0], token[1])
                    signal.static = False



                    # Convert the binary ndarray to a list of string representations of each row
                    temp1 = [''.join(str(x) for x in row) for row in arb_id.boolean_matrix[:, token[0]:token[1] + 1]]
                    temp2 = zeros((temp1.__len__()+1), dtype=uint64)
                    # convert each string representation to int
                    for i, row in enumerate(temp1):
                        temp2[i] = int(row, 2)

                    temp3 = integrate.cumtrapz(temp2)
                    print("Arb Id " + str(k) + ", Signal from " + str(token[0]) + " to  " + str(token[1]) + " Integrated successfully")



                    # create an unsigned integer pandas.Series using the time index from this Arb ID's original data.
                    signal.time_series = Series(temp3[:], index=arb_id.original_data.index, dtype=float64)



                    # Normalize the signal and update its meta-data
                    signal.normalize_and_set_metadata(normalize_strategy)
                    # add this signal to the signal dictionary which is keyed by Arbitration ID
                    if (k * 256) in transform_dict:
                        transform_dict[k * 256][(arb_id.id * 256, signal.start_index, signal.stop_index)] = signal
                    else:
                        print("Successfully added at transform dict")
                        transform_dict[k * 256] = {(arb_id.id * 256, signal.start_index, signal.stop_index): signal}

                    a_timer.set_token_to_signal()

    a_timer.set_signal_generation()

    return transform_dict


def transform_signals(a_timer: PipelineTimer,
                      arb_id_dict: dict,
                      transform_pickle_filename: str,
                      normalize_strategy,
                      force=False):
    if force and path.isfile(transform_pickle_filename):
        remove(transform_pickle_filename)
    if path.isfile(transform_pickle_filename):
            print("\nSignal transformation already completed and forcing is turned off. Using pickled data...")
            return load(open(transform_pickle_filename, "rb"))

    a_timer.start_function_time()

    transform_dict = {}  # arb_id_dict

    for k, arb_id in arb_id_dict.items():
        if not arb_id.static:
            for token in arb_id.tokenization:
                a_timer.start_iteration_time()

                signal = Signal(k * 256, token[0], token[1])



                # Convert the binary ndarray to a list of string representations of each row
                temp1 = [''.join(str(x) for x in row) for row in arb_id.boolean_matrix[:, token[0]:token[1] + 1]]
                temp2 = zeros((temp1.__len__()+1), dtype=uint64)
                # convert each string representation to int
                for i, row in enumerate(temp1):
                    temp2[i] = int(row, 2)

                temp3 = integrate.cumtrapz(temp2)



                # create an unsigned integer pandas.Series using the time index from this Arb ID's original data.
                signal.time_series = Series(temp3[:], index=arb_id.original_data.index, dtype=float64)



                # Normalize the signal and update its meta-data
                signal.normalize_and_set_metadata(normalize_strategy)
                # add this signal to the signal dictionary which is keyed by Arbitration ID
                if k in transform_dict:
                    transform_dict[k][(arb_id.id, signal.start_index, signal.stop_index)] = signal
                else:
                    transform_dict[k] = {(arb_id.id, signal.start_index, signal.stop_index): signal}

                a_timer.set_token_to_signal()

    a_timer.set_signal_generation()

    return transform_dict
