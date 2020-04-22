from pandas import DataFrame, read_csv, Series
from numpy import int64
from os import path, remove
from pickle import load
from typing import Callable
from ArbID import ArbID
from J1979 import J1979
from PipelineTimer import PipelineTimer


class PreProcessor:
    def __init__(self, data_filename: str, id_output_filename: str, j1979_output_filename: str):
        self.data_filename:         str = data_filename
        self.id_output_filename:    str = id_output_filename
        self.j1979_output_filename: str = j1979_output_filename
        self.data:                  DataFrame = None
        self.import_time:           float = 0.0
        self.dictionary_time:       float = 0.0
        self.total_time:            float = 0.0

    def import_csv(self, a_timer: PipelineTimer, filename):

        def hex2int(x):
            if x == '':
                return 0
            return int(x, 16)

        def fix_time(x):
            try:
                return float(str(x)[:-1])
            except ValueError:
                # There may have been a newline the capture device was trying to write when turned off.
                return None

        # Used by pd.read_csv to apply the functions to the respective column vectors in the .csv file
        convert_dict = {'time': fix_time, 'id': hex2int, 'dlc': hex2int, 'b0': hex2int, 'b1': hex2int, 'b2': hex2int,
                        'b3': hex2int, 'b4': hex2int, 'b5': hex2int, 'b6': hex2int, 'b7': hex2int}

        print("\nReading in " + self.data_filename + "...")

        a_timer.start_function_time()

        self.data = read_csv(filename,
                             header=None,
                             names=['time', 'id', 'dlc', 'b0', 'b1',
                                    'b2', 'b3', 'b4', 'b5', 'b6', 'b7'],
                             skiprows=7,
                             delim_whitespace=True,
                             converters=convert_dict,
                             index_col=0)

        print(self.data)

        a_timer.set_can_csv_to_df()

        # sanity check output of the original data
        # print("\nSample of the original data:")
        # print(self.data.head(5), "\n")

    @staticmethod
    def generate_j1979_dictionary(j1979_data: DataFrame) -> dict:

        d = {}
        services = j1979_data.groupby('b2')
        for uds_pid, data in services:
            d[uds_pid] = J1979(uds_pid, data)
        return d

    def generate_arb_id_dictionary(self,
                                   a_timer:                     PipelineTimer,
                                   normalize_strategy:          Callable,
                                   time_conversion:             int = 1000,
                                   freq_analysis_accuracy:      float = 0.0,
                                   freq_synchronous_threshold:  float = 0.0,
                                   force:                       bool = False) -> (dict, dict):
        if path.isfile(self.id_output_filename):
            if force:
                # Remove any existing pickled Arb ID dictionary and create one based on this data.
                remove(self.id_output_filename)
                remove(self.j1979_output_filename)
                self.import_csv(a_timer, self.data_filename)
            else:
                arb_id_dict = load(open(self.id_output_filename, "rb"))
                j1979_dict = load(open(self.j1979_output_filename, "rb"))
                return arb_id_dict, j1979_dict
        else:
            self.import_csv(a_timer, self.data_filename)

        id_dictionary = {}
        j1979_dictionary = {}

        a_timer.start_function_time()

        for arb_id in Series.unique(self.data['id']):
            if isinstance(arb_id, int64):
                if arb_id == 2015:
                    # This is the J1979 requests (if any) (ID 0x7DF = 2015). Just ignore it.
                    continue
                elif arb_id == 2024:
                    # This is the J1979 responses (ID 0x7DF & 0x8 = 0x7E8 = 2024)
                    j1979_data = self.data.loc[self.data['id'] == arb_id].copy(
                    )
                    j1979_data.drop('dlc', axis=1, inplace=True)
                    j1979_data.drop('id', axis=1, inplace=True)
                    a_timer.start_nested_function_time()
                    j1979_dictionary = self.generate_j1979_dictionary(
                        j1979_data)
                    a_timer.set_j1979_creation()
                elif arb_id > 0:
                    a_timer.start_iteration_time()

                    this_id = ArbID(arb_id)
                    this_id.original_data = self.data.loc[self.data['id'] == arb_id]
                    this_id.original_data = this_id.original_data.copy()  # type: DataFrame

                    # Check if the Arbitration ID always used the same DLC. If not, ignore it.
                    # We can effectively ignore this Arb ID by not adding it to the Arb ID dictionary.
                    if this_id.original_data['dlc'].nunique() != 1:
                        continue
                    this_id.dlc = this_id.original_data['dlc'].iloc[0]
                    this_id.original_data.drop('dlc', axis=1, inplace=True)
                    this_id.original_data.drop('id', axis=1, inplace=True)

                    # If DLC < 8, we can automatically drop data column vectors > DLC.
                    # E.G. drop bytes "B7" and "B6" if DLC is 6; those are padding data injected by can-dump and were
                    # not actually on the bus.
                    if this_id.dlc < 8:
                        for i in range(this_id.dlc, 8):
                            this_id.original_data.drop(
                                'b' + str(i), axis=1, inplace=True)

                    # Check if there are duplicate index values and correct them.
                    if not this_id.original_data.index.is_unique:
                        correction_mask = this_id.original_data.index.duplicated()
                        this_id.original_data = this_id.original_data[~correction_mask]

                    this_id.generate_binary_matrix_and_tang(
                        a_timer, normalize_strategy)
                    this_id.analyze_transmission_frequency(time_convert=time_conversion,
                                                           ci_accuracy=freq_analysis_accuracy,
                                                           synchronous_threshold=freq_synchronous_threshold)
                    id_dictionary[arb_id] = this_id

                    a_timer.set_arb_id_creation()

        a_timer.set_raw_df_to_arb_id_dict()

        return id_dictionary, j1979_dictionary
