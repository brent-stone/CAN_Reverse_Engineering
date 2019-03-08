from time import time
from typing import List


class PipelineTimer:
    def __init__(self, verbose: bool = True):
        self.verbose:               bool = verbose
        self.function_time:         float = 0.0
        self.nested_function_time:  float = 0.0
        self.iteration_time:        float = 0.0
        self.nested_iteration_time: float = 0.0

        # Pre-Processing Timings
        self.can_csv_to_df:         float = 0.0
        self.raw_df_to_arb_id_dict: float = 0.0
        self.arb_id_creation:       List[float] = []
        self.j1979_creation:        float = 0.0
        self.hex_to_bool_matrix:    List[float] = []
        self.bool_matrix_to_tang:   List[float] = []
        self.plot_save_j1979_dict:  float = 0.0
        self.plot_save_j1979_pid:   List[float] = []

        # Lexical Analysis Timings
        self.tokenization:          float = 0.0
        self.tang_to_composition:   List[float] = []
        self.composition_merge:     List[float] = []
        self.signal_generation:     float = 0.0
        self.token_to_signal:       List[float] = []
        self.plot_save_arb_id_dict: float = 0.0
        self.plot_save_arb_id:      List[float] = []

        # Semantic Analysis Timings
        self.subset_selection:      float = 0.0
        self.plot_save_cluster_dict: float = 0.0
        self.label_propagation:     float = 0.0
        self.plot_save_cluster:     List[float] = []

    def start_function_time(self):
        self.function_time = time()

    def start_nested_function_time(self):
        self.nested_function_time = time()

    def start_iteration_time(self):
        self.iteration_time = time()

    def start_nested_iteration_time(self):
        self.nested_iteration_time = time()

    #               Pre-Processing Timings                #

    # Called in PreProcessor.import_csv
    def set_can_csv_to_df(self):
        self.can_csv_to_df = time() - self.function_time
        if self.verbose:
            print("\n" + str(self.can_csv_to_df) + " seconds to import and format raw data into a DataFrame")

    # Called in PreProcessor.generate_arb_id_dictionary
    def set_raw_df_to_arb_id_dict(self):
        self.raw_df_to_arb_id_dict = time() - self.function_time
        if self.verbose:
            print("\n" + str(self.raw_df_to_arb_id_dict) +
                  " seconds to produce arbitration ID dictionary, boolean matrices, and TANGs")

    # Called in the loop within PreProcessor.generate_arb_id_dictionary
    def set_arb_id_creation(self):
        self.arb_id_creation.append(time() - self.iteration_time)

    def set_j1979_creation(self):
        self.j1979_creation = time() - self.nested_function_time
        if self.verbose:
            print("\n" + str(self.j1979_creation) + " seconds to process J1979 response data into a dictionary")

    # Called in ArbID.generate_binary_matrix_and_tang
    def set_hex_to_bool_matrix(self):
        self.hex_to_bool_matrix.append(self.nested_function_time - time())

    # Called in ArbID.generate_binary_matrix_and_tang
    def set_bool_matrix_to_tang(self):
        self.bool_matrix_to_tang.append(self.nested_function_time - time())

    # Called in the Plotter.py plot_j1979 function.
    def set_plot_save_j1979_dict(self):
        self.plot_save_j1979_dict = time() - self.function_time
        if self.verbose:
            print("\n" + str(self.plot_save_j1979_dict) + " seconds to plot and save the J1979 response data")

    # Called in the loop within the Plotter.py plot_j1979 function.
    def set_plot_save_j1979_pid(self):
        self.plot_save_j1979_pid.append(time() - self.iteration_time)

    #               Lexical Analysis Timings                #

    # Called in the LexicalAnalysis.py tokenize_dictionary function.
    def set_tokenization(self):
        self.tokenization = time() - self.function_time
        if self.verbose:
            print("\n" + str(self.tokenization) + " seconds to tokenize the arbitration ID dictionary using TANGs")

    # Called in the loop within the LexicalAnalysis.py tokenize_dictionary function.
    def set_tang_to_composition(self):
        self.tang_to_composition.append(time() - self.iteration_time)

    # Called in the loop within the LexicalAnalysis.py tokenize_dictionary function.
    def set_composition_merge(self):
        self.composition_merge.append(time() - self.iteration_time)

    # Called in the LexicalAnalysis.py generate_signals function.
    def set_signal_generation(self):
        self.signal_generation = time() - self.function_time
        if self.verbose:
            print("\n" + str(self.signal_generation) +
                  " seconds to generate signals and their statistics using token compositions.")

    # Called in the loop within the LexicalAnalysis.py generate_signals function.
    def set_token_to_signal(self):
        self.token_to_signal.append(time() - self.iteration_time)

    # Called in the Plotter.py plot_signals_by_arb_id function.
    def set_plot_save_arb_id_dict(self):
        self.plot_save_arb_id_dict = time() - self.function_time
        if self.verbose:
            print("\n" + str(self.plot_save_arb_id_dict) + " seconds to plot and save the Signals and TANGs by Arb ID")

    # Called in the loop within the Plotter.py plot_signals_by_arb_id function.
    def set_plot_save_arb_id(self):
        self.plot_save_arb_id.append(time() - self.iteration_time)

    #               Semantic Analysis Timings                #

    # Called in the SemanticAnalysis.py subset_correlation function.
    def set_subset_selection(self):
        self.subset_selection = time() - self.function_time

    # Called in the SemanticAnalysis.py label_propagation function.
    def set_label_propagation(self):
        self.label_propagation = time() - self.function_time
        if self.verbose:
            print("\n" + str(self.label_propagation) + " seconds to perform label propagation.")

    # Called in the Plotter.py plot_signals_by_cluster function.
    def set_plot_save_cluster_dict(self):
        self.plot_save_cluster_dict = time() - self.function_time
        if self.verbose:
            print("\n" + str(self.plot_save_cluster_dict) + " seconds to plot and save the clusters.")

    # Called in the loop within the Plotter.py plot_signals_by_cluster function.
    def set_plot_save_cluster(self):
        self.plot_save_cluster.append(time() - self.iteration_time)
