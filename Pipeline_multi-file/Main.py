from FileBoi import FileBoi
from Sample import Sample
# from Plotter import plot_sample_threshold_heatmap

# Cross validation parameters for finding an optimal tokenization inversion distance threshold -- NOT WORKING?
kfold_n: int = 5
current_vehicle_number = 0

good_boi = FileBoi()
samples = good_boi.go_fetch(kfold_n)
for key, sample_list in samples.items():  # type: tuple, list
    for sample in sample_list:  # type: Sample
        print(current_vehicle_number)
        print("\nData import and Pre-Processing for " + sample.output_vehicle_dir)
        id_dict, j1979_dict = sample.pre_process()
        if j1979_dict:
            sample.plot_j1979(j1979_dict, vehicle_number=str(current_vehicle_number))

        # The following 3-lines of code were intended to find good settings for TANG inversions.... it didn't work?
        # print("\nFinding optimal lexical analysis threshold parameters for " + sample.output_vehicle_dir)
        # sample.find_lex_thresholds(id_dict)
        # plot_sample_threshold_heatmap(sample)

        #                 LEXICAL ANALYSIS                     #
        print("\n\t##### BEGINNING LEXICAL ANALYSIS OF " + sample.output_vehicle_dir + " #####")
        sample.tokenize_dictionary(id_dict)
        signal_dict = sample.generate_signals(id_dict, bool(j1979_dict))
        sample.plot_arb_ids(id_dict, signal_dict, vehicle_number=str(current_vehicle_number))

        #                 LEXICAL ANALYSIS                     #
        print("\n\t##### BEGINNING SEMANTIC ANALYSIS OF " + sample.output_vehicle_dir + " #####")
        corr_matrix, combined_df = sample.generate_correlation_matrix(signal_dict)
        if j1979_dict:
            signal_dict, j1979_correlation = sample.j1979_labeling(j1979_dict, signal_dict, combined_df)
        cluster_dict, linkage_matrix = sample.cluster_signals(corr_matrix)
        sample.plot_clusters(cluster_dict, signal_dict, bool(j1979_dict), vehicle_number=str(current_vehicle_number))
        sample.plot_dendrogram(linkage_matrix, vehicle_number=str(current_vehicle_number))
        current_vehicle_number += 1
