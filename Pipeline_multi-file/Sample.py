from PreProcessor import PreProcessor
from Validator import Validator
from LexicalAnalysis import tokenize_dictionary, generate_signals
from SemanticAnalysis import generate_correlation_matrix, signal_clustering, j1979_signal_labeling
from Plotter import plot_j1979, plot_signals_by_arb_id, plot_signals_by_cluster, plot_dendrogram
from sklearn.preprocessing import minmax_scale
from typing import Callable
from PipelineTimer import PipelineTimer
from os import chdir, mkdir, path, remove
from pickle import dump, load
from numpy import ndarray, zeros, float16
from pandas import DataFrame

# File names for the on-disc data input and output.
output_folder:              str = 'output'
pickle_arb_id_filename:     str = 'pickleArbIDs.p'
pickle_threshold_filename:  str = 'pickleLexThresholds.p'
pickle_j1979_filename:      str = 'pickleJ1979.p'
pickle_signal_filename:     str = 'pickleSignals.p'
pickle_subset_filename:     str = 'pickleSubset.p'
csv_corr_matrix_filename:   str = 'subset_correlation_matrix.csv'
pickle_j1979_corr_matrix:   str = 'pickleJ1979_correlation.p'
pickle_clusters_filename:   str = 'pickleClusters.p'
pickle_linkage_filename:    str = 'pickleLinkage.p'
pickle_combined_df_filename: str = 'pickleCombinedDataFrame.p'
csv_all_signals_filename:   str = 'complete_correlation_matrix.csv'
pickle_timer_filename:      str = 'pickleTimer.p'

dump_to_pickle:             bool = True

# Change out the normalization strategies as needed.
tang_normalize_strategy:    Callable = minmax_scale
signal_normalize_strategy:  Callable = minmax_scale

# Turn on or off portions of the pipeline and output methods using these flags.
force_pre_processing:       bool = False
force_threshold_search:     bool = False
force_threshold_plotting:   bool = False
force_j1979_plotting:       bool = True
use_j1979:                  bool = True

force_lexical_analysis:     bool = False
force_signal_generation:    bool = False
force_arb_id_plotting:      bool = True

force_correlation_matrix:   bool = False
force_clustering:           bool = False
force_signal_labeling:      bool = False
use_j1979_tags_in_plots:    bool = True
force_cluster_plotting:     bool = True
force_dendrogram_plotting:  bool = True

# Parameters and threshold used for Arb ID transmission frequency analysis during Pre-processing.
time_conversion = 1000  # convert seconds to milliseconds
z_lookup = {.8: 1.28, .9: 1.645, .95: 1.96, .98: 2.33, .99: 2.58}
freq_analysis_accuracy = z_lookup[0.9]
freq_synchronous_threshold = 0.1

# Threshold parameters used during lexical analysis.
tokenization_bit_distance:  float = 0.2
tokenize_padding:           bool = True
merge_tokens:               bool = True

# Threshold parameters used during semantic analysis
subset_selection_size:      float = 0.25
max_intra_cluster_distance: float = 0.20
min_j1979_correlation:      float = 0.85
# fuzzy_labeling:             bool = True


# A timer class to record timings throughout the pipeline.
a_timer = PipelineTimer(verbose=True)


class Sample:
    def __init__(self, make: str, model: str, year: str, sample_index: str, sample_path: str, kfold_n: int):
        # Sample Specific Meta-Data
        self.make:                      str = make
        self.model:                     str = model
        self.year:                      str = year
        self.path:                      str = sample_path
        self.output_vehicle_dir:        str = make + "_" + model + "_" + year
        self.output_sample_dir:         str = sample_index
        # Pre-Processing Settings
        self.use_j1979:                 bool = use_j1979
        self.force_threshold_plot:      bool = force_threshold_plotting
        self.avg_score_matrix:          ndarray = zeros((1, 1), dtype=float16)
        # Lexical analysis settings
        self.tang_inversion_bit_dist:   float = tokenization_bit_distance
        self.use_padding:               bool = tokenize_padding
        self.merge_tokens:              bool = merge_tokens
        self.token_merge_dist:          float = tokenization_bit_distance
        # Semantic analysis settings
        self.max_inter_cluster_dist:    float = max_intra_cluster_distance
        # Various comparison testing methods are implemented in the Validator class
        self.validator:                 Validator = Validator(use_j1979, kfold_n)

    def make_and_move_to_vehicle_directory(self):
        # This drills down three directories to './output/make_model_year/sample_index/' Make directories as needed
        if not path.exists(output_folder):
            mkdir(output_folder)
        chdir(output_folder)
        if not path.exists(self.output_vehicle_dir):
            mkdir(self.output_vehicle_dir)
        chdir(self.output_vehicle_dir)
        if not path.exists(self.output_sample_dir):
            mkdir(self.output_sample_dir)
        chdir(self.output_sample_dir)

    @staticmethod
    def move_back_to_parent_directory():
        # Move back to root of './output/make_model_year/sample_index/"
        chdir("../../../")

    def pre_process(self):
        self.make_and_move_to_vehicle_directory()
        pre_processor = PreProcessor(self.path, pickle_arb_id_filename, pickle_j1979_filename, self.use_j1979)
        id_dictionary, j1979_dictionary = pre_processor.generate_arb_id_dictionary(a_timer,
                                                                                   tang_normalize_strategy,
                                                                                   time_conversion,
                                                                                   freq_analysis_accuracy,
                                                                                   freq_synchronous_threshold,
                                                                                   force_pre_processing)
        if dump_to_pickle:
            if force_pre_processing:
                if path.isfile(pickle_arb_id_filename):
                    remove(pickle_arb_id_filename)
                if path.isfile(pickle_j1979_filename):
                    remove(pickle_j1979_filename)
            # Lexical analysis will add additional information to the Arb ID dict. Don't dump if you're going to
            # immediately delete and replace pickle_arb_id_filename during Lexical Analysis.
            if not force_lexical_analysis:
                if not path.isfile(pickle_arb_id_filename) and id_dictionary:
                    print("\nDumping arb ID dictionary for " + self.output_vehicle_dir + " to " +
                          pickle_arb_id_filename)
                    dump(id_dictionary, open(pickle_arb_id_filename, "wb"))
                    print("\tComplete...")
                if not path.isfile(pickle_j1979_filename) and j1979_dictionary:
                    print("\nDumping J1979 dictionary for " + self.output_vehicle_dir + " to " + pickle_j1979_filename)
                    dump(j1979_dictionary, open(pickle_j1979_filename, "wb"))
                    print("\tComplete...")
        self.move_back_to_parent_directory()
        return id_dictionary, j1979_dictionary

    def plot_j1979(self, j1979_dictionary: dict, vehicle_number: str):
        self.make_and_move_to_vehicle_directory()
        plot_j1979(a_timer, j1979_dictionary, vehicle_number, force_j1979_plotting)
        self.move_back_to_parent_directory()

    def find_lex_thresholds(self, id_dict: dict):
        self.make_and_move_to_vehicle_directory()
        if path.isfile(pickle_threshold_filename):
            if force_threshold_search:
                # Remove any existing pickled threshold parameter search result matrix and create one.
                remove(pickle_threshold_filename)
            else:
                print("\n\tLex threshold search already completed and forcing is turned off. Using pickled data...")
                self.avg_score_matrix = load(open(pickle_threshold_filename, "rb"))
                self.validator.set_lex_threshold_parameters(self)
                # Move back to root of './output/make_model_year/sample_index/"
                self.move_back_to_parent_directory()
                return

        self.validator.k_fold_lex_threshold_selection(id_dict=id_dict, sample=self)

        if not path.isfile(pickle_threshold_filename):
            print("\nDumping lexical analysis threshold search matrix for " + self.output_vehicle_dir +
                  " to " + pickle_threshold_filename)
            dump(self.avg_score_matrix, open(pickle_threshold_filename, "wb"))
            print("\tComplete...")

        self.move_back_to_parent_directory()

    def tokenize_dictionary(self, id_dictionary: dict):
        # Using force_pre_processing = True and force_lexical_analysis = False will cause the 2nd condition to trigger.
        if force_lexical_analysis or not path.isfile(pickle_arb_id_filename):
            tokenize_dictionary(a_timer=a_timer, d=id_dictionary, force=force_lexical_analysis,
                                include_padding=self.use_padding, merge=self.merge_tokens,
                                max_distance=self.tang_inversion_bit_dist)
        if dump_to_pickle:
            self.make_and_move_to_vehicle_directory()
            if force_lexical_analysis:
                if path.isfile(pickle_arb_id_filename):
                    remove(pickle_arb_id_filename)
            if not path.isfile(pickle_arb_id_filename) and id_dictionary:
                print("\nDumping arb ID dictionary for " + self.output_vehicle_dir + " to " + pickle_arb_id_filename)
                dump(id_dictionary, open(pickle_arb_id_filename, "wb"))
                print("\tComplete...")
            self.move_back_to_parent_directory()

    def generate_signals(self, id_dictionary: dict, postpone_pickle: bool = False):
        self.make_and_move_to_vehicle_directory()
        signal_dict = generate_signals(a_timer=a_timer,
                                       arb_id_dict=id_dictionary,
                                       signal_pickle_filename=pickle_signal_filename,
                                       normalize_strategy=signal_normalize_strategy,
                                       force=force_signal_generation)
        # postpone_pickle is simply a check whether J1979 data was present in the sample. If it was present, then wait
        # to save out the signal_dictionary until correlated Signals are labeled by sample.j1979_labeling().
        if dump_to_pickle and not postpone_pickle and not path.isfile(pickle_signal_filename):
            print("\nDumping signal dictionary for " + self.output_vehicle_dir + " to " + pickle_signal_filename)
            dump(signal_dict, open(pickle_signal_filename, "wb"))
            print("\tComplete...")
        self.move_back_to_parent_directory()
        return signal_dict

    def plot_arb_ids(self, id_dictionary: dict, signal_dictionary: dict, vehicle_number: str):
        self.make_and_move_to_vehicle_directory()
        plot_signals_by_arb_id(a_timer=a_timer,
                               arb_id_dict=id_dictionary,
                               signal_dict=signal_dictionary,
                               vehicle_number=vehicle_number,
                               force=force_arb_id_plotting)
        self.move_back_to_parent_directory()

    def generate_correlation_matrix(self, signal_dictionary: dict):
        self.make_and_move_to_vehicle_directory()
        if dump_to_pickle and force_correlation_matrix:
            if path.isfile(csv_corr_matrix_filename):
                remove(csv_corr_matrix_filename)
        corr_matrix, combined_df = generate_correlation_matrix(a_timer=a_timer,
                                                               csv_signals_correlation_filename=csv_corr_matrix_filename,
                                                               combined_df_filename=pickle_combined_df_filename,
                                                               signal_dict=signal_dictionary,
                                                               force=force_correlation_matrix)
        if not path.isfile(csv_corr_matrix_filename) and not corr_matrix.empty:
            print("\nDumping subset correlation matrix for " + self.output_vehicle_dir + " to " +
                  csv_corr_matrix_filename)
            corr_matrix.to_csv(csv_corr_matrix_filename)
            print("\tComplete...")
        if not path.isfile(pickle_combined_df_filename) and not combined_df.empty:
            print("\nDumping combined signal DataFrame matrix for " + self.output_vehicle_dir + " to " +
                  pickle_combined_df_filename)
            dump(combined_df, open(pickle_combined_df_filename, "wb"))
            print("\tComplete...")
        self.move_back_to_parent_directory()
        return corr_matrix, combined_df

    def cluster_signals(self, corr_matrix: DataFrame):
        self.make_and_move_to_vehicle_directory()
        cluster_dict, linkage_matrix = signal_clustering(corr_matrix,
                                                         self.max_inter_cluster_dist,
                                                         pickle_clusters_filename,
                                                         pickle_linkage_filename,
                                                         force_clustering)  # type: dict, ndarray
        # Before we return or save the clusters, lets remove all singleton clusters. This serves as an implicit
        # filtering technique for incorrectly tokenized signals.
        list_to_remove = []
        for k, cluster in cluster_dict.items():
            if len(cluster) < 2:
                list_to_remove.append(k)
        for k in list_to_remove:
            cluster_dict.pop(k, None)

        if not path.isfile(pickle_clusters_filename) and cluster_dict:
            print("\nDumping cluster dictionary to " + pickle_clusters_filename)
            dump(cluster_dict, open(pickle_clusters_filename, "wb"))
            print("\tComplete...")
        if not path.isfile(pickle_linkage_filename):
            print("\nDumping agglomerative clustering linkage matrix to " + pickle_linkage_filename)
            dump(linkage_matrix, open(pickle_linkage_filename, "wb"))
            print("\tComplete...")

        self.move_back_to_parent_directory()
        return cluster_dict, linkage_matrix

    def j1979_labeling(self, j1979_dictionary: dict, signal_dictionary: dict, combined_df: DataFrame):
        self.make_and_move_to_vehicle_directory()
        signal_dictionary, j1979_correlation_matrix = j1979_signal_labeling(a_timer=a_timer,
                                                                            j1979_corr_filename=pickle_j1979_corr_matrix,
                                                                            signal_filename=pickle_signal_filename,
                                                                            df_signals=combined_df,
                                                                            j1979_dict=j1979_dictionary,
                                                                            signal_dict=signal_dictionary,
                                                                            correlation_threshold=min_j1979_correlation,
                                                                            force=force_signal_generation)
        # If the signal dictionary pickled data was deleted because j1979 tagging needed to happen, then save it with
        # the tags added by the call to j1979_signal_labeling().
        if not path.isfile(pickle_signal_filename) and signal_dictionary and j1979_dictionary:
            print("\nDumping J1979 tagged signal dictionary to " + pickle_signal_filename)
            dump(signal_dictionary, open(pickle_signal_filename, "wb"))
            print("\tComplete...")
        if not path.isfile(pickle_j1979_corr_matrix):
            print("\nDumping j1979 signal correlation matrix to " + pickle_j1979_corr_matrix)
            dump(j1979_correlation_matrix, open(pickle_j1979_corr_matrix, "wb"))
            print("\tComplete...")
        self.move_back_to_parent_directory()
        return signal_dictionary, j1979_correlation_matrix

    def plot_clusters(self, cluster_dictionary: dict, signal_dictionary: dict, use_j1979_tags: bool,
                      vehicle_number: str):
        self.make_and_move_to_vehicle_directory()
        plot_signals_by_cluster(a_timer=a_timer,
                                cluster_dict=cluster_dictionary,
                                signal_dict=signal_dictionary,
                                use_j1979_tags=use_j1979_tags,
                                vehicle_number=vehicle_number,
                                force=force_cluster_plotting)
        self.move_back_to_parent_directory()

    def plot_dendrogram(self, linkage_matrix: ndarray, vehicle_number: str):
        self.make_and_move_to_vehicle_directory()
        plot_dendrogram(a_timer=a_timer, linkage_matrix=linkage_matrix, threshold=self.max_inter_cluster_dist,
                        vehicle_number=vehicle_number, force=force_dendrogram_plotting)
        self.move_back_to_parent_directory()
