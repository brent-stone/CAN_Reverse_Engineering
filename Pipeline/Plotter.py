import matplotlib.pyplot as plt
from matplotlib.pyplot import savefig
from numpy import where, isin, ndarray
from os import chdir, mkdir, path
from shutil import rmtree
from PipelineTimer import PipelineTimer


figure_format:  str = "png"  # png works well for quickly previewing results and draft results write ups.
# figure_format:  str = "eps"  # Journals/Conferences generally prefer EPS file format for camera-ready copies.
figure_dpi:     int = 300
figure_transp:  bool = False

arb_id_folder:  str = 'figures'
cluster_folder: str = 'clusters'
j1979_folder:   str = 'j1979'


def plot_signals_by_arb_id(a_timer: PipelineTimer, arb_id_dict: dict, signal_dict: dict, force: bool=False):
    if path.exists(arb_id_folder):
        if force:
            rmtree(arb_id_folder)
        else:
            print("\nArbID plotting appears to have already been done and forcing is turned off. Skipping...")
            return

    a_timer.start_function_time()

    for k_id, signals in signal_dict.items():
        arb_id = arb_id_dict[k_id]
        if not arb_id.static:
            print("Plotting Arb ID " + str(k_id) + " (" + str(hex(k_id)) + ")")
            a_timer.start_iteration_time()

            signals_to_plot = []
            # Don't plot the static signals
            for k_signal, signal in signals.items():
                if not signal.static:
                    signals_to_plot.append(signal)
            # One row per signal plus one for the TANG
            fig, axes = plt.subplots(nrows=1 + len(signals_to_plot), ncols=1)
            if not isinstance(axes, ndarray):
                print("Static signal. No figures to plot")
                continue

            plt.suptitle("Time Series and TANG for Arbitration ID " + hex(k_id),
                         weight='bold',
                         position=(0.5, 1))
            fig.set_size_inches(8, (1 + len(signals_to_plot) + 1) * 1.3)
            # The min() statement provides whitespace for the title depending on the number of subplots.
            size_adjust = len(signals_to_plot) / 100
            plt.tight_layout(h_pad=1, rect=(0, 0, 1, min(0.985, 0.93 + size_adjust)))
            # This adjusts whitespace padding on the left and right of the subplots
            fig.subplots_adjust(left=0.07, right=0.98)
            for i, signal in enumerate(signals_to_plot):
                ax = axes[i]
                ax.set_title(signal.plot_title,
                             style='italic',
                             size='medium')
                ax.set_xlim([signal.time_series.first_valid_index(), signal.time_series.last_valid_index()])
                ax.plot(signal.time_series, color='black')
                # Add a 25% opacity dashed black line to the entropy gradient plot at one boundary of each sub-flow
                axes[-1].axvline(x=signal.start_index, alpha=0.25, c='black', linestyle='dashed')

            # Plot the entropy gradient at the bottom of the overall output
            ax = axes[-1]
            ax.set_title("Min-Max Normalized Transition Aggregation N-Gram (TANG)",
                         style='italic',
                         size='medium')
            tang_bit_width = arb_id.tang.shape[0]
            ax.set_xlim([-0.01 * tang_bit_width, 1.005 * tang_bit_width])
            y = arb_id.tang[:]
            # Differentiate bit positions with non-zero and zero entropy using black points and grey x respectively.
            ix = isin(y, 0)
            pad_bit = where(ix)
            non_pad_bit = where(~ix)
            ax.scatter(non_pad_bit, y[non_pad_bit], color='black', marker='o', s=10)
            ax.scatter(pad_bit, y[pad_bit], color='grey', marker='^', s=10)

            if not path.exists(arb_id_folder):
                mkdir(arb_id_folder)
            chdir(arb_id_folder)

            # If you want transparent backgrounds, a different file format, etc. then change these settings accordingly.
            savefig(hex(arb_id.id) + "." + figure_format,
                    bbox_iches='tight',
                    pad_inches=0.0,
                    dpi=figure_dpi,
                    format=figure_format,
                    transparent=figure_transp)

            chdir("..")

            plt.close(fig)

            a_timer.set_plot_save_arb_id()
            print("\tComplete...")

    a_timer.set_plot_save_arb_id_dict()


def plot_signals_by_cluster(a_timer: PipelineTimer,
                            cluster_dict: dict,
                            signal_dict: dict,
                            use_j1979_tags: bool,
                            force: bool=False):
    if path.exists(cluster_folder):
        if force:
            rmtree(cluster_folder)
        else:
            print("\nCluster plotting appears to have already been done and forcing is turned off. Skipping...")
            return

    a_timer.start_function_time()

    print("\n")
    for cluster_number, list_of_signals in cluster_dict.items():
        print("Plotting cluster", cluster_number, "with " + str(len(list_of_signals)) + " signals.")
        a_timer.start_iteration_time()

        # Setup the plot
        fig, axes = plt.subplots(nrows=len(list_of_signals), ncols=1, squeeze=False)
        plt.suptitle("Cluster Number " + str(cluster_number),
                     weight='bold',
                     position=(0.5, 1))
        fig.set_size_inches(8, (1 + len(list_of_signals)+1) * 1.3)

        size_adjust = len(list_of_signals) / 100
        # The min() statement provides whitespace for the suptitle depending on the number of subplots.
        plt.tight_layout(h_pad=1, rect=(0, 0, 1, min(0.985, 0.93 + size_adjust)))
        # This adjusts whitespace padding on the left and right of the subplots
        fig.subplots_adjust(left=0.07, right=0.98)

        # Plot the time series of each signal in the cluster
        for i, signal_key in enumerate(list_of_signals):
            signal = signal_dict[signal_key[0]][signal_key]
            ax = axes[i, 0]
            if signal.j1979_title and use_j1979_tags:
                this_title = signal.plot_title + " [" + signal.j1979_title + \
                             " (PCC:" + str(round(signal.j1979_pcc, 2)) + ")]"
            else:
                this_title = signal.plot_title
            ax.set_title(this_title,
                         style='italic',
                         size='medium')
            ax.set_xlim([signal.time_series.first_valid_index(), signal.time_series.last_valid_index()])
            ax.plot(signal.time_series, color='black')

        if not path.exists(cluster_folder):
            mkdir(cluster_folder)
        chdir(cluster_folder)

        # If you want transparent backgrounds, a different file format, etc. then change these settings accordingly.
        savefig("cluster_" + str(cluster_number) + "." + figure_format,
                bbox_iches='tight',
                pad_inches=0.0,
                dpi=figure_dpi,
                format=figure_format,
                transparent=figure_transp)

        chdir("..")

        plt.close(fig)

        a_timer.set_plot_save_cluster()
        print("\tComplete...")

    a_timer.set_plot_save_cluster_dict()


def plot_j1979(a_timer: PipelineTimer, j1979_dict: dict, force: bool=False):
    if path.exists(j1979_folder):
        if force:
            rmtree(j1979_folder)
        else:
            print("\nJ1979 plotting appears to have already been done and forcing is turned off. Skipping...")
            return

    a_timer.start_function_time()

    print("Plotting J1979 response data")
    plot_length = len(j1979_dict.keys())

    # Setup the plot
    fig, axes = plt.subplots(nrows=plot_length, ncols=1, squeeze=False)
    plt.suptitle("J1979 Data",
                 weight='bold',
                 position=(0.5, 1))
    fig.set_size_inches(8, (1 + plot_length) * 1.3)

    size_adjust = plot_length / 100
    # The min() statement provides whitespace for the suptitle depending on the number of subplots.
    plt.tight_layout(h_pad=1, rect=(0, 0, 1, min(0.985, 0.93 + size_adjust)))
    # This adjusts whitespace padding on the left and right of the subplots
    fig.subplots_adjust(left=0.07, right=0.98)

    # Plot the time series of each signal in the cluster
    for i, (pid, data) in enumerate(j1979_dict.items()):
        a_timer.start_iteration_time()
        ax = axes[i, 0]
        ax.set_title("PID " + str(hex(pid)) + ": " + data.title,
                     style='italic',
                     size='medium')
        ax.set_xlim([data.data.first_valid_index(), data.data.last_valid_index()])
        ax.plot(data.data, color='black')
        a_timer.set_plot_save_j1979_pid()

    if not path.exists(j1979_folder):
        mkdir(j1979_folder)
    chdir(j1979_folder)

    # If you want transparent backgrounds, a different file format, etc. then change these settings accordingly.
    savefig("j1979." + figure_format,
            bbox_iches='tight',
            pad_inches=0.0,
            dpi=figure_dpi,
            format=figure_format,
            transparent=figure_transp)

    chdir("..")

    plt.close(fig)

    a_timer.set_plot_save_j1979_dict()
    print("\tComplete...")
