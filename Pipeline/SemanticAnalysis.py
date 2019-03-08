from pandas import concat, DataFrame, read_csv
from numpy import zeros
from os import path, remove
from pickle import load
from ast import literal_eval
from J1979 import J1979
from Signal import Signal
from PipelineTimer import PipelineTimer


def subset_selection(a_timer:       PipelineTimer,
                     signal_dict:   dict = None,
                     subset_pickle: str = "",
                     force:         bool = False,
                     subset_size:   float = 0.25) -> DataFrame:

    if path.isfile(subset_pickle):
        if force:
            # Remove any existing pickled Signal dictionary and create one.
            remove(subset_pickle)
        else:
            print("\nSubset selection already completed and forcing is turned off. Using pickled data...")
            return load(open(subset_pickle, "rb"))

    a_timer.start_function_time()

    signal_index = 0
    for k_arb_id, arb_id_signals in signal_dict.items():
        for k_signal_id, signal in arb_id_signals.items():
            if not signal.static:
                signal_index += 1

    # setup subset selection data structure
    df: DataFrame = DataFrame(zeros((signal_index, 4)),
                              columns=["arb_id", "start_index", "stop_index", "Shannon_Index"])

    for i, (k_arb_id, arb_id_signals) in enumerate(signal_dict.items()):
        for j, (k_signal_id, signal) in enumerate(arb_id_signals.items()):
            if not signal.static:
                df.iloc[signal_index-1] = [k_arb_id, signal.start_index, signal.stop_index, signal.shannon_index]
                signal_index -= 1

    # sort by Shannon Index
    df.sort_values(by="Shannon_Index", inplace=True, ascending=False)

    # Select subset with largest Shannon Index Values
    df = df.head(int(round(df.__len__() * subset_size, 0)))

    # In order to make an arb ID sorted output, sort this subset by arb_id
    df.sort_values(by="arb_id", inplace=True)

    # Re-index each Signal in the subset using the Signal with the most observed samples. Prepare to create a DataFrame
    # that can be used for generating a correlation matrix.
    subset = []
    subset_cols = []
    largest_index = []

    for index, row in df.iterrows():
        signal_id = (int(row[0]), int(row[1]), int(row[2]))
        signal = signal_dict[row[0]][signal_id]
        subset.append(signal)
        subset_cols.append(signal_id)
        if signal.time_series.__len__() > largest_index.__len__():
            largest_index = signal.time_series.index

    subset_df: DataFrame = DataFrame(zeros((largest_index.__len__(), subset.__len__())),
                                     columns=subset_cols,
                                     index=largest_index)

    for signal in subset:
        signal_id = (signal.arb_id, signal.start_index, signal.stop_index)
        subset_df[signal_id] = signal.time_series.reindex(index=largest_index, method='nearest')

    a_timer.set_subset_selection()

    return subset_df


def subset_correlation(subset: DataFrame,
                       csv_correlation_filename: str,
                       force: bool = False) -> DataFrame:
    if not force and path.isfile(csv_correlation_filename):
        print("\nA subset correlation appears to exist and forcing is turned off. Using " + csv_correlation_filename)
        # Read the .csv into a DataFrame. Also, we need to convert the columns and index from strings back to tuples.
        # Pandas.read_csv brings the data in as a DataFrame. Pandas.DataFrame.rename converts the columns and index with
        # ast.literal_eval. Literal_eval will convert a string representation of a tuple back to an actual tuple.
        return read_csv(csv_correlation_filename, index_col=0).rename(index=literal_eval, columns=literal_eval)
    else:
        return subset.corr()


def greedy_signal_clustering(correlation_matrix: DataFrame = None,
                             correlation_threshold: float = 0.8,
                             fuzzy_labeling: bool = True) -> dict:

    correlation_keys = correlation_matrix.columns.values
    previously_clustered_signals = {}
    cluster_dict = {}
    new_cluster_label = 0

    for n, row in enumerate(correlation_keys):
        for m, col in enumerate(correlation_keys):
            if n == m:
                # this is a diagonal on the correlation matrix. Skip it.
                continue
            # I chose to round here to allow relationships 'oh so close' to making it. No reason this HAS to be done.
            result = round(correlation_matrix.iloc[n, m], 2)

            # check if this is a significant correlation according to our heuristic threshold.
            if result >= correlation_threshold:
                # Check if the current row signal is currently unlabeled
                if row not in previously_clustered_signals.keys():
                    # Check if the current col signal is currently unlabeled
                    if col not in previously_clustered_signals.keys():
                        # Both signals are unlabeled. Create a new one.
                        cluster_dict[new_cluster_label] = [row, col]
                        previously_clustered_signals[row] = {new_cluster_label}
                        previously_clustered_signals[col] = {new_cluster_label}
                        # print("created new cluster #", new_cluster_label, cluster_dict[new_cluster_label])
                        new_cluster_label += 1
                    else:
                        # Row isn't labeled but col is; add row to all of col's clusters.
                        # print("adding", row, "to clusters", previously_clustered_signals[col])
                        # row is not already in a cluster, add it to col's set of clusters
                        for label in previously_clustered_signals[col]:
                            cluster_dict[label].append(row)
                        previously_clustered_signals[row] = previously_clustered_signals[col]
                else:
                    # Check if the current col signal is currently unlabeled
                    if col not in previously_clustered_signals.keys():
                        # Row if labeled but col is not; add col to row's set of clusters
                        # print("adding", col, "to clusters", previously_clustered_signals[row])
                        for label in previously_clustered_signals[row]:
                            cluster_dict[label].append(col)
                        previously_clustered_signals[col] = previously_clustered_signals[row]
                    # Both signals are already labeled
                    else:
                        # Check if we're using fuzzy labeling (a signal can belong to multiple clusters).
                        # If so, check if the union of both sets of labels is the empty set. If so, this is a
                        # relationship that hasn't already been captures by an existing cluster. Make a new one.
                        if fuzzy_labeling:
                            row_label_set = previously_clustered_signals[row]
                            col_label_set = previously_clustered_signals[col]
                            if not row_label_set & col_label_set:
                                cluster_dict[new_cluster_label] = [row, col]
                                previously_clustered_signals[row] = {new_cluster_label} | row_label_set
                                previously_clustered_signals[col] = {new_cluster_label} | col_label_set
                                # print("created new cluster #", new_cluster_label, cluster_dict[new_cluster_label])
                                new_cluster_label += 1
                            else:
                                # We're using fuzzy labeling and these two signals represent a 'bridge' between two
                                # signal clusters. Fold col into row's clusters and delete col's unique cluster indices.
                                for label in row_label_set - col_label_set:
                                    cluster_dict[label].append(col)
                                previously_clustered_signals[col] = row_label_set | col_label_set
                                for label in col_label_set - row_label_set:
                                    cluster_dict[label].append(row)
                                previously_clustered_signals[row] = row_label_set | col_label_set
                        # print(row, col, "already in cluster_dict", previously_clustered_signals[row], "&",
                        #       previously_clustered_signals[col])

    # Delete any duplicate clusters
    cluster_sets = []
    deletion_labels = []
    for label, cluster in cluster_dict.items():
        this_set = set(cluster)
        if this_set in cluster_sets:
            deletion_labels.append(label)
        else:
            cluster_sets.append(this_set)
    for label in deletion_labels:
        del cluster_dict[label]

    return cluster_dict


# NOTE: This method has a LOT of redundancy with the subset_selection, signal_correlation, and greedy_signal_clustering
# logic. If you know you always want to perform label propagation, it would be more efficient to incorporate it directly
# into those functions. Since this code base is more of a Proof of Concept, label propagation is deliberately pulled
# out as a distinct method to make the pipeline steps as distinct as possible.
def label_propagation(a_timer:                          PipelineTimer,
                      pickle_clusters_filename:         str = '',
                      pickle_all_signals_df_filename:   str = '',
                      csv_signals_correlation_filename: str = '',
                      signal_dict:                      dict = None,
                      cluster_dict:                     dict = None,
                      correlation_threshold:            float = 0.8,
                      force:                            bool = False):
    if path.isfile(pickle_all_signals_df_filename) and path.isfile(csv_signals_correlation_filename):
        if force:
            # Remove any existing data.
            remove(pickle_all_signals_df_filename)
            remove(csv_signals_correlation_filename)
            remove(pickle_clusters_filename)
        else:
            print("\nA DataFrame and correlation matrix for label propagation appears to exist and forcing is turned "
                  "off. Using " + pickle_all_signals_df_filename + ", " + csv_signals_correlation_filename + ", and "
                  + pickle_clusters_filename)
            return [load(open(pickle_all_signals_df_filename, "rb")),
                    read_csv(csv_signals_correlation_filename, index_col=0).rename(index=literal_eval,
                                                                                   columns=literal_eval),
                    load(open(pickle_clusters_filename, "rb"))]

    a_timer.start_function_time()

    non_static_signals_dict = {}
    largest_index = []
    df_columns = []

    # Put all non-static signals into one DataFrame. Re-index all of them to share the same index.
    for k_arb_id, arb_id_signals in signal_dict.items():
        for k_signal_id, signal in arb_id_signals.items():
            if not signal.static:
                non_static_signals_dict[k_signal_id] = signal
                df_columns.append(k_signal_id)
                if signal.time_series.__len__() > largest_index.__len__():
                    largest_index = signal.time_series.index

    df: DataFrame = DataFrame(zeros((largest_index.__len__(), df_columns.__len__())),
                              columns=df_columns,
                              index=largest_index)

    for k_signal_id, signal in non_static_signals_dict.items():
        df[k_signal_id] = signal.time_series.reindex(index=largest_index, method='nearest')

    # Calculate the correlation matrix for this DataFrame of all non-static signals.
    correlation_matrix = df.corr()

    # Re-run the algorithm from greedy_signal_clustering but omitting the logic for creating new clusters.
    # This effectively propagates the labels generated by the subset of signals with the largest Shannon Index values
    # to any correlated signals which were not part of that subset.
    correlation_keys = correlation_matrix.columns.values
    previously_clustered_signals = {}
    for k_cluster_id, cluster in cluster_dict.items():
        for k_signal_id in cluster:
            previously_clustered_signals[k_signal_id] = k_cluster_id

    for n, row in enumerate(correlation_keys):
        for m, col in enumerate(correlation_keys):
            if n == m:
                # this is a diagonal on the correlation matrix. Skip it.
                continue
            # I chose to round here to allow relationships 'oh so close' to making it. No reason this HAS to be done.
            result = round(correlation_matrix.iloc[n, m], 2)

            # check if this is a significant correlation according to our heuristic threshold.
            if result >= correlation_threshold:
                # if row signal is already a member of a cluster
                if row in previously_clustered_signals.keys():
                    # if col signal is already a member of a cluster
                    if col in previously_clustered_signals.keys():
                        # print(row, col, "already in clusters", previously_clustered_signals[row], "&",
                        #       previously_clustered_signals[col])
                        continue
                    # if col is not already in a cluster, add it to row's cluster
                    else:
                        # print("adding", col, "to cluster", clusters[previously_clustered_signals[row]])
                        cluster_dict[previously_clustered_signals[row]].append(col)
                        previously_clustered_signals[col] = previously_clustered_signals[row]
                # row signal hasn't been added to a cluster
                else:
                    # if col signal is already a member of a cluster
                    if col in previously_clustered_signals.keys():
                        # print("adding", row, "to cluster", clusters[previously_clustered_signals[col]])
                        # row is not already in a cluster, add it to col's cluster
                        cluster_dict[previously_clustered_signals[col]].append(row)
                        previously_clustered_signals[row] = previously_clustered_signals[col]

    a_timer.set_label_propagation()

    df.dropna(axis=0, how='any', inplace=True)
    df.dropna(axis=1, how='any', inplace=True)

    return df, correlation_matrix, cluster_dict


def j1979_signal_labeling(a_timer:               PipelineTimer,
                          j1979_corr_filename:   str = "",
                          df_signals:            DataFrame = None,
                          j1979_dict:            dict = None,
                          signal_dict:           dict = None,
                          correlation_threshold: float = 0.8,
                          force:                 bool = False):

    if path.isfile(j1979_corr_filename):
        if force:
            # Remove any existing data.
            remove(j1979_corr_filename)
        else:
            print("\nA J1979 correlation matrix for signal labeling appears to exist and forcing is turned off. Using "
                  + j1979_corr_filename)
            return signal_dict, load(open(j1979_corr_filename, "rb"))

    latest_start_index = 0.0
    earliest_end_index = 99999999999999.9
    df_columns = []

    for pid, pid_data in j1979_dict.items():  # type: int, J1979
        if latest_start_index < pid_data.data.index[0]:
            latest_start_index = pid_data.data.index[0]
        if earliest_end_index > pid_data.data.index[-1]:
            earliest_end_index = pid_data.data.index[-1]
        df_columns.append(pid_data.title)

    df_signals = df_signals.loc[latest_start_index:earliest_end_index]  # type: DataFrame

    df_j1979: DataFrame = DataFrame(zeros((df_signals.shape[0], df_columns.__len__())),
                                    columns=df_columns,
                                    index=df_signals.index)

    for pid, pid_data in j1979_dict.items():  # type: int, J1979
        df_j1979[pid_data.title] = pid_data.data.reindex(index=df_signals.index, method='nearest')

    df_combined = concat([df_signals, df_j1979], axis=1)

    correlation_matrix = df_combined.corr()

    correlation_matrix.dropna(axis=1, how='all', inplace=True)
    correlation_matrix.dropna(axis=0, how='all', inplace=True)

    # Just consider the J1979 column correlations. Slice off the identity rows at the end of the DataFrame as well.
    for index, row in correlation_matrix[df_columns][:-len(df_columns)].iterrows():
        row = abs(row)
        max_index = row.idxmax(axis=1, skipna=True)
        if row[max_index] >= correlation_threshold:
            signal = signal_dict[index[0]][index]  # type: Signal
            # print("Adding J1979 attribute " + max_index + " to signal ID " + str(index))
            signal.j1979_title = max_index
            signal.j1979_pcc = row[max_index]
            signal_dict[index[0]][index] = signal

            # print(i, index, row[max_index], max_index, row.values)

    return signal_dict, correlation_matrix[df_columns][:-len(df_columns)]

    # correlation_matrix.to_csv('j1979_correlation.csv')
