from numpy import float64, nditer, uint64, zeros
from pandas import Series
from os import path, remove
from pickle import load
from ArbID import ArbID
from Signal import Signal
from PipelineTimer import PipelineTimer


def tokenize_dictionary(a_timer:            PipelineTimer,
                        d:                  dict,
                        force:              bool = False,
                        include_padding:    bool = False,
                        merge:              bool = True,
                        max_distance:       float= 0.1):
    a_timer.start_function_time()

    for k, arb_id in d.items():
        if not arb_id.static:
            if arb_id.padding and not force:
                print("\nTokenization already completed and forcing is turned off. Skipping...")
                return
            a_timer.start_iteration_time()
            get_composition(arb_id, include_padding, max_distance)
            a_timer.set_tang_to_composition()
            if merge:
                a_timer.start_iteration_time()
                merge_tokens(arb_id, max_distance)
                a_timer.set_composition_merge()
    a_timer.set_tokenization()


# This is a greedy algorithm to cluster bit positions in a series of CAN payloads suspected of being part of a
# continuous numerical time series.
def get_composition(arb_id: ArbID, include_padding=False, max_inversion_distance: float = 0.0):
    tokens = []
    start_index = 0
    currently_clustering = False
    big_endian = True
    last_bit_position = 0

    # Consider each element in the TANG. The TANG is an ndarray with index being bit position from the
    # original CAN data. The cell value is the observed transition frequency for that bit position.
    for i, bit_position in enumerate(nditer(arb_id.tang)):
        # Is this a padding bit?
        if bit_position <= 0.000001:
            arb_id.padding.append(i)
            # Are we clustering padding bits? If so, proceed to the normal clustering logic. Else, do the following.
            if not include_padding:
                if currently_clustering:
                    # This is padding, we're already clustering, and we're not clustering padding; save the token.
                    tokens.append((start_index, i - 1))
                    currently_clustering = False
                    start_index = i + 1
                    last_bit_position = bit_position
                continue

        # Are we still enlarging the current token?
        if currently_clustering:
            if bit_position >= last_bit_position and big_endian:
                pass
            elif bit_position <= last_bit_position and not big_endian:
                pass
            # Are we allowing inversions (max_inversion_distance > 0)? If so, check if this inversion is acceptable.
            elif abs(bit_position-last_bit_position) <= max_inversion_distance:
                pass
            # Is this the second bit position we need to establish the endian of the signal?
            elif start_index == i - 1:
                if bit_position >= last_bit_position:
                    big_endian = True
                else:
                    big_endian = False
            # This is an unacceptable transition frequency inversion, save the current token and start a new one
            else:
                tokens.append((start_index, i - 1))
                start_index = i
        # We aren't currently clustering and we intend to cluster this bit position
        else:
            currently_clustering = True
            start_index = i

        last_bit_position = bit_position

    # We reached the last bit position while clustering. Add this final token.
    if currently_clustering:
        tokens.append((start_index, arb_id.tang.__len__() - 1))

    arb_id.tokenization = tokens


def merge_tokens(arb_id: ArbID, max_distance):
    # if arb_id.id == 292:  # make this equal to the decimal value of an Arb ID in the data you want to see get merged
    #     verbose = True
    # else:
    verbose = False
    if verbose:
        print("\nENTERING MERGE PHASE OF ARB ID", arb_id.id)
        print("STARTING TOKENS:", arb_id.tokenization)

    if arb_id.static or arb_id.tokenization.__len__() < 2:
        # Make sure there's multiple tokens to marge
        pass
    else:
        # Editing data structures while iterating over them is a bad idea in Python
        # Instead, lets keep track of tokens we want to delete using remove_list.
        remove_list = []
        last = None
        for i, token in enumerate(arb_id.tokenization):
            if verbose:
                print("Last:", last, "\tCurrent:", token)
            if last:
                # Are these tokens adjacent?
                if last[1] + 1 == token[0]:
                    if verbose:
                        print("\tAdjacent with distance of", abs(arb_id.tang[last[1]] - arb_id.tang[token[0]]))
                    # Is the transition frequency of the adjacent bit positions less than the max distance threshold?
                    if abs(arb_id.tang[last[1]] - arb_id.tang[token[0]]) <= max_distance:
                        remove_list.append(last)
                        token = (last[0], token[1])
                        arb_id.tokenization[i] = token
                        if verbose:
                            print("\t\tMerged into", token)
            last = token
        if remove_list:
            for token in remove_list:
                arb_id.tokenization.remove(token)
            if verbose:
                print("final tokenization", arb_id.tokenization)


# noinspection PyTypeChecker
def          generate_signals(a_timer: PipelineTimer,
                     arb_id_dict: dict,
                     signal_pickle_filename: str,
                     normalize_strategy,
                     force=False):
    if path.isfile(signal_pickle_filename):
        if force:
            # Remove any existing pickled Signal dictionary and create one.
            remove(signal_pickle_filename)
        else:
            print("\nSignal generation already completed and forcing is turned off. Using pickled data...")
            return load(open(signal_pickle_filename, "rb"))

    a_timer.start_function_time()

    signal_dict = {}

    for k, arb_id in arb_id_dict.items():
        if not arb_id.static:
            for token in arb_id.tokenization:
                a_timer.start_iteration_time()

                signal = Signal(k, token[0], token[1])

                # Convert the binary ndarray to a list of string representations of each row
                temp1 = [''.join(str(x) for x in row) for row in arb_id.boolean_matrix[:, token[0]:token[1] + 1]]
                temp2 = zeros((temp1.__len__(), 1), dtype=uint64)
                # convert each string representation to int
                for i, row in enumerate(temp1):
                    temp2[i] = int(row, 2)

                # create an unsigned integer pandas.Series using the time index from this Arb ID's original data.
                signal.time_series = Series(temp2[:, 0], index=arb_id.original_data.index, dtype=float64)
                # Normalize the signal and update its meta-data
                signal.normalize_and_set_metadata(normalize_strategy)
                # add this signal to the signal dictionary which is keyed by Arbitration ID
                if k in signal_dict:
                    signal_dict[k][(arb_id.id, signal.start_index, signal.stop_index)] = signal
                else:
                    signal_dict[k] = {(arb_id.id, signal.start_index, signal.stop_index): signal}

                a_timer.set_token_to_signal()

    a_timer.set_signal_generation()

    return signal_dict
