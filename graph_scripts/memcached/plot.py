
import os
import pandas as pd
import matplotlib.pyplot as plt
put_legend = False
# 4 plot fig size, text sizes, etc.
four_plot_fig_x = 7
four_plot_fig_y = 4
four_plot_fig_text = 32
four_plot_fig_tick = 30 # maybe increase this to 28 too
four_plot_fig_legend = 30

efficiency_plot_x = 11
efficiency_plot_y = 5
efficiency_plot_text = 22
efficiency_plot_tick = 22
efficiency_plot_legend = 22
efficiency_plot_marker = 12

sensitivity_x = 8
sensitivity_y = 4
sensitivity_text = 20
sensitivity_tick = 20
sensitivity_legend = 18

grid_major_width = 1.0
grid_minor_width = 0.01

axis_text_size = four_plot_fig_text
tick_text_size = four_plot_fig_tick
legend_text_size = four_plot_fig_legend

end_to_end_zoomx = (0.9, 1.65)
end_to_end_zoomy = (0.9, 1.3)

minor_grid = False
major_grid_color = "lightgray"

import os
import pandas as pd
import matplotlib.pyplot as plt

memcached = True
service_time = 1
if service_time == 10:
    bw_target = 80
    file_load = "100k"
elif service_time == 1:
    bw_target = 45
if memcached:
    bw_target = 25

# Configurable variables for enabling or disabling schedulers
enable_caladan = True
enable_shenango = True
enable_coresync = True
enable_shenango_fix = False
enable_delay_05 = False
enable_delay_10 = False
enable_utilization_range = True
enable_static = True

# Time window settings (modify as needed)
if memcached:
    start_time = 20040000
elif service_time == 10:
    start_time = 9000000
elif service_time == 1:
    start_time = 9000000
time_window = 200

count = 1

colors = {
    'ias': 'b',
    'simple': 'r',
    'ias park': 'g',
    'simple park': 'teal',
    'delay 0.5': 'yellow',
    'util': 'purple',
    'spin': 'black'
}

# Mapping directory keywords to scheduler names
scheduler_map = {
    'ias': 'Caladan',
    'simple': 'Shenango',
    'ias park': 'CoreSync',
    'simple park': 'Shenango_fix',
    'delay 0.5': 'Delay Range',
    'util': 'Utilization Range',
    'spin': 'Static'
}

# Schedulers enabled or disabled
enabled_schedulers = {
    "delay 0.5": enable_delay_05,
    "delay 1.0": enable_delay_10,
    "ias": enable_caladan,
    "ias park": enable_coresync,
    "simple": enable_shenango,
    "simple park": enable_shenango_fix,
    "util": enable_utilization_range,
    "spin": enable_static
}

# Directories to process
if memcached:
    directories = {
        "delay 0.5": 'memcached_breakwater_25_50_500k_16cores_100conns_11nodes_delay_range_0.5_1.0',
        "delay 1.0": 'memcached_breakwater_25_50_500k_16cores_100conns_11nodes_delay_range_1.0_4.0',
        "ias": 'memcached_breakwater_25_50_500k_16cores_100conns_11nodes_ias',
        "ias park": 'memcached_breakwater_25_50_500k_16cores_100conns_11nodes_ias_park_0.075_15',
        "simple": 'memcached_breakwater_25_50_500k_16cores_100conns_11nodes_simple',
        "simple park": 'memcached_breakwater_25_50_500k_16cores_100conns_11nodes_simple_park_0.075_15',
        "util": 'memcached_breakwater_25_50_500k_16cores_100conns_11nodes_utilization_range_0.75_0.95',
        "spin": 'memcached_breakwater_25_50_guaranteed_spinning_500k_16cores_100conns_11nodes_simple'
    }
elif service_time == 10:
    directories = {
        "delay 0.5": 'breakwater_{}_{}_{}_16cores_100conns_11nodes_delay_range_0.5_1.0'.format(bw_target, bw_target*2, file_load),
        "delay 1.0": 'breakwater_{}_{}_{}_16cores_100conns_11nodes_delay_range_1.0_4.0'.format(bw_target, bw_target*2, file_load),
        "ias": 'breakwater_{}_{}_{}_16cores_100conns_11nodes_ias'.format(bw_target, bw_target*2, file_load),
        "ias park": 'breakwater_{}_{}_{}_16cores_100conns_11nodes_ias_park_0.4_15'.format(bw_target, bw_target*2, file_load),
        "simple": 'breakwater_{}_{}_{}_16cores_100conns_11nodes_simple'.format(bw_target, bw_target*2, file_load),
        "simple park": 'breakwater_{}_{}_{}_16cores_100conns_11nodes_simple_park_0.4_15'.format(bw_target, bw_target*2, file_load),
        "util": 'breakwater_{}_{}_{}_16cores_100conns_11nodes_utilization_range_0.75_0.95'.format(bw_target, bw_target*2, file_load),
        "spin": 'breakwater_{}_{}_guaranteed_spinning_{}_16cores_100conns_11nodes_simple'.format(bw_target, bw_target*2, file_load)
    }

metric_labels = {
    "credit_pool": "Total Credits",
    "credit_used": "Credits Issued",
    "delay": "Queue Delay (us)",
    "num_cores": "Cores"
}

# CSV file names to process (1000k, 2000k, 4000k)
if memcached:
    csv_files = ['1000k_timeseries.csv', '2000k_timeseries.csv', '4000k_timeseries.csv']
elif service_time == 10:
    csv_files = ['300k_timeseries.csv', '600k_timeseries.csv', '1300k_timeseries.csv']

# Metrics to plot
metrics = [ 'num_cores'] # 'credit_pool', 'credit_used', 'delay',

# Output directory for plots
output_dir = 'plots'
os.makedirs(output_dir, exist_ok=True)

# Function to plot a specific metric
def plot_metric(data, scheduler, metric, time_range, ax):
    ax.tick_params(axis='both', which='major', labelsize=tick_text_size)
    # ax.xaxis.get_major_formatter().set_offset_string("")
    if metric == 'num_cores':
        ax.set_ylim(0, 17)
        ax.set_yticks([0, 4, 8, 12, 16])
    ax.plot(data['timestamp'], data[metric], color=colors[scheduler], label=scheduler_map[scheduler], linestyle='dashed')
    ax.set_xlim([time_range[0], time_range[1]])
    ax.set_xlabel('Time (us)', fontsize=four_plot_fig_text)
    ax.set_ylabel(metric_labels[metric], fontsize=four_plot_fig_text)
    ax.xaxis.get_offset_text().set_color('white')
    # ax.xaxis.get_offset_text().set_text('')

# Main plotting loop
for metric in metrics:
    for csv_file in csv_files:
        fig, ax = plt.subplots(1, 1, figsize=(four_plot_fig_x, four_plot_fig_y))

        for key, directory in directories.items():
            if not enabled_schedulers[key]:
                continue

            # Construct file path and read data
            file_path = os.path.join(directory, csv_file)
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)

                # Filter the data for the time window
                df = df[(df['timestamp'] >= start_time) & (df['timestamp'] <= start_time + time_window)]
                df = df.sort_values(df.columns[0], ascending =True)
                # Plot the metric for the scheduler
                plot_metric(df, key, metric, (start_time, start_time + time_window), ax)
        
        # Add legend only for 1000k.csv plots
        
        if memcached:
            if put_legend and '1000k' in csv_file and metric != "num_cores":
                ax.legend(fontsize=legend_text_size, handlelength=0.75, loc="lower right",
                    borderpad=0.1,labelspacing=0, handletextpad=0.3)
        elif service_time == 10:
            if put_legend and '600k' in csv_file and metric != "num_cores":
                ax.legend(fontsize=legend_text_size, handlelength=0.75, loc="lower right",
                    borderpad=0.1,labelspacing=0, handletextpad=0.3)

        # Save the plot to a PDF
        pdf_filename = f'{metric}_{csv_file.split(".")[0]}.pdf'
        # plt.savefig(os.path.join(output_dir, pdf_filename))
        plt.savefig("{}/{}.pdf".format(output_dir,pdf_filename), format='pdf', bbox_inches="tight")
        plt.close(fig)
        print("done with plot {}".format(count))
        count += 1

print(f"Plots saved to {output_dir}")

