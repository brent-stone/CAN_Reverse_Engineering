import argparse
from os import chdir, mkdir, path, remove
from pickle import dump
from sklearn.preprocessing import minmax_scale
from typing import Callable
from PreProcessor import PreProcessor
from LexicalAnalysis import tokenize_dictionary, generate_signals
from SemanticAnalysis import subset_selection, subset_correlation, greedy_signal_clustering, label_propagation, \
    j1979_signal_labeling
from Plotter import plot_j1979, plot_signals_by_arb_id, plot_signals_by_cluster
from PipelineTimer import PipelineTimer
from FromCanUtilsLog import canUtilsToTSV

# File names for the on-disc data input and output.
# Input:

# get filename from argument parser
parser = argparse.ArgumentParser()
parser.add_argument("filename", nargs='*', type=str,
                    help="filename of CAN log file")
parser.add_argument(
    "-c", "--can-utils", help="read file in Linux can-utils format", action="store_true")

args = parser.parse_args()

# degault to "loggerProgram0.log" if no filename specified by args
can_data_filename = args.filename[0] if args.filename else "loggerProgram0.log"

if (args.can_utils):
    # run converter to convert to TSV before continuing
    can_data_filename = canUtilsToTSV(can_data_filename)

# Output:
output_folder:              str = 'output'
pickle_arb_id_filename:     str = 'pickleArbIDs.p'
pickle_j1979_filename:      str = 'pickleJ1979.p'
pickle_signal_filename:     str = 'pickleSignals.p'
pickle_subset_filename:     str = 'pickleSubset.p'
csv_correlation_filename:   str = 'subset_correlation_matrix.csv'
pickle_j1979_correlation:   str = 'pickleJ1979_correlation.p'
pickle_clusters_filename:   str = 'pickleClusters.p'
pickle_all_signal_filename: str = 'pickleAllSignalsDataFrame.p'
csv_all_signals_filename:   str = 'complete_correlation_matrix.csv'
pickle_timer_filename:      str = 'pickleTimer.p'

# Change out the normalization strategies as needed.
tang_normalize_strategy:    Callable = minmax_scale
signal_normalize_strategy:  Callable = minmax_scale

# Turn on or off portions of the pipeline and output methods using these flags.
force_pre_processing:       bool = False
force_j1979_plotting:       bool = False

force_lexical_analysis:     bool = False
force_arb_id_plotting:      bool = True

force_semantic_analysis:    bool = False
force_signal_labeling:      bool = False
use_j1979_tags_in_plots:    bool = True
force_cluster_plotting:     bool = False

dump_to_pickle:             bool = True

# Parameters and threshold used for Arb ID transmission frequency analysis during Pre-processing.
time_conversion = 1000  # convert seconds to milliseconds
z_lookup = {.8: 1.28, .9: 1.645, .95: 1.96, .98: 2.33, .99: 2.58}
freq_analysis_accuracy = z_lookup[0.9]
freq_synchronous_threshold = 0.1

# Threshold parameters used during lexical analysis.
tokenization_bit_distance:  float = 0.2
tokenize_padding:           bool = True

# Threshold parameters used during semantic analysis
subset_selection_size:      float = 0.25
fuzzy_labeling:             bool = True
min_correlation_threshold:  float = 0.85

# A timer class to record timings throughout the pipeline.
a_timer = PipelineTimer(verbose=True)

#            DATA IMPORT AND PRE-PROCESSING             #
pre_processor = PreProcessor(
    can_data_filename, pickle_arb_id_filename, pickle_j1979_filename)
id_dictionary, j1979_dictionary = pre_processor.generate_arb_id_dictionary(a_timer,
                                                                           tang_normalize_strategy,
                                                                           time_conversion,
                                                                           freq_analysis_accuracy,
                                                                           freq_synchronous_threshold,
                                                                           force_pre_processing)
if j1979_dictionary:
    plot_j1979(a_timer, j1979_dictionary, force_j1979_plotting)


#                 LEXICAL ANALYSIS                     #
print("\n\t\t\t##### BEGINNING LEXICAL ANALYSIS #####")
tokenize_dictionary(a_timer,
                    id_dictionary,
                    force_lexical_analysis,
                    include_padding=tokenize_padding,
                    merge=True,
                    max_distance=tokenization_bit_distance)
signal_dictionary = generate_signals(a_timer,
                                     id_dictionary,
                                     pickle_signal_filename,
                                     signal_normalize_strategy,
                                     force_lexical_analysis)
plot_signals_by_arb_id(a_timer, id_dictionary,
                       signal_dictionary, force_arb_id_plotting)

#                  SEMANTIC ANALYSIS                    #
print("\n\t\t\t##### BEGINNING SEMANTIC ANALYSIS #####")
subset_df = subset_selection(a_timer,
                             signal_dictionary,
                             pickle_subset_filename,
                             force_semantic_analysis,
                             subset_size=subset_selection_size)
corr_matrix_subset = subset_correlation(
    subset_df, csv_correlation_filename, force_semantic_analysis)
cluster_dict = greedy_signal_clustering(corr_matrix_subset,
                                        correlation_threshold=min_correlation_threshold,
                                        fuzzy_labeling=fuzzy_labeling)
df_full, corr_matrix_full, cluster_dict = label_propagation(a_timer,
                                                            pickle_clusters_filename=pickle_clusters_filename,
                                                            pickle_all_signals_df_filename=pickle_all_signal_filename,
                                                            csv_signals_correlation_filename=csv_all_signals_filename,
                                                            signal_dict=signal_dictionary,
                                                            cluster_dict=cluster_dict,
                                                            correlation_threshold=min_correlation_threshold,
                                                            force=force_semantic_analysis)
signal_dictionary, j1979_correlations = j1979_signal_labeling(a_timer=a_timer,
                                                              j1979_corr_filename=pickle_j1979_correlation,
                                                              df_signals=df_full,
                                                              j1979_dict=j1979_dictionary,
                                                              signal_dict=signal_dictionary,
                                                              correlation_threshold=min_correlation_threshold,
                                                              force=force_signal_labeling)
plot_signals_by_cluster(a_timer, cluster_dict, signal_dictionary,
                        use_j1979_tags_in_plots, force_cluster_plotting)

#                     DATA STORAGE                      #
if dump_to_pickle:
    if force_pre_processing:
        if path.isfile(pickle_arb_id_filename):
            remove(pickle_arb_id_filename)
        if path.isfile(pickle_j1979_filename):
            remove(pickle_j1979_filename)
    if force_lexical_analysis or force_signal_labeling:
        if path.isfile(pickle_signal_filename):
            remove(pickle_signal_filename)
    if force_semantic_analysis:
        if path.isfile(pickle_subset_filename):
            remove(pickle_subset_filename)
        if path.isfile(csv_correlation_filename):
            remove(csv_correlation_filename)
        if path.isfile(pickle_j1979_correlation):
            remove(pickle_j1979_correlation)
        if path.isfile(pickle_clusters_filename):
            remove(pickle_clusters_filename)
        if path.isfile(pickle_all_signal_filename):
            remove(pickle_all_signal_filename)
        if path.isfile(csv_all_signals_filename):
            remove(csv_all_signals_filename)

    timer_flag = 0
    if not path.exists(output_folder):
        mkdir(output_folder)
    chdir(output_folder)
    if not path.isfile(pickle_arb_id_filename):
        timer_flag += 1
        print("\nDumping arb ID dictionary to " + pickle_arb_id_filename)
        dump(id_dictionary, open(pickle_arb_id_filename, "wb"))
        print("\tComplete...")
    if not path.isfile(pickle_j1979_filename):
        timer_flag += 1
        print("\nDumping J1979 dictionary to " + pickle_j1979_filename)
        dump(j1979_dictionary, open(pickle_j1979_filename, "wb"))
        print("\tComplete...")
    if not path.isfile(pickle_signal_filename):
        timer_flag += 1
        print("\nDumping signal dictionary to " + pickle_signal_filename)
        dump(signal_dictionary, open(pickle_signal_filename, "wb"))
        print("\tComplete...")
    if not path.isfile(pickle_subset_filename):
        timer_flag += 1
        print("\nDumping signal subset list to " + pickle_subset_filename)
        dump(subset_df, open(pickle_subset_filename, "wb"))
        print("\tComplete...")
    if not path.isfile(csv_correlation_filename):
        timer_flag += 1
        print("\nDumping subset correlation matrix to " + csv_correlation_filename)
        corr_matrix_subset.to_csv(csv_correlation_filename)
        print("\tComplete...")
    if not path.isfile(pickle_j1979_correlation):
        timer_flag += 1
        print("\nDumping J1979 correlation DataFrame to " +
              pickle_j1979_correlation)
        dump(j1979_correlations, open(pickle_j1979_correlation, "wb"))
        print("\tComplete...")
    if not path.isfile(pickle_clusters_filename):
        timer_flag += 1
        print("\nDumping cluster dictionary to " + pickle_clusters_filename)
        dump(cluster_dict, open(pickle_clusters_filename, "wb"))
        print("\tComplete...")
    if not path.isfile(pickle_all_signal_filename):
        timer_flag += 1
        print("\nDumping complete signals DataFrame to " +
              pickle_all_signal_filename)
        dump(df_full, open(pickle_all_signal_filename, "wb"))
        print("\tComplete...")
    if not path.isfile(csv_all_signals_filename):
        timer_flag += 1
        print("\nDumping complete correlation matrix to " +
              csv_all_signals_filename)
        corr_matrix_full.to_csv(csv_all_signals_filename)
        print("\tComplete...")
    if timer_flag == 9:
        print("\nDumping pipeline timer to " + pickle_timer_filename)
        dump(a_timer, open(pickle_timer_filename, "wb"))
        print("\tComplete...")
    chdir("..")
