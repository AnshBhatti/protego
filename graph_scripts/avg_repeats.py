import os
import pandas as pd
import numpy as np

# Define the root directory
root_dir = "."  # Change to your actual base directory path

# Define the subfolders where the data is stored, along with their corresponding labels
subfolders = {
    "memcached_breakwater_25_50_guaranteed_spinning_2000k_16cores_100conns_11nodes_simple": "spin",
    "memcached_breakwater_25_50_2000k_16cores_100conns_11nodes_utilization_range_0.75_0.95": "util",
    "memcached_breakwater_25_50_2000k_16cores_100conns_11nodes_simple": "simple",
    "memcached_breakwater_25_50_2000k_16cores_100conns_11nodes_ias_park_0.075_15": "ias_park",
    "memcached_breakwater_25_50_2000k_16cores_100conns_11nodes_ias": "ias"
}

# Output CSV file
output_csv = "compiled_stats.csv"

# Define the "desired" offered_load values (fixed)
desired_loads = [2000000, 2500000, 3000000, 3500000, 4000000]

# Create an empty DataFrame to store the results
compiled_data = pd.DataFrame(columns=["subfolder_type", "desired", "offered_load_mean", "offered_load_median", "throughput_mean", "throughput_median", "throughput_min"])

# Iterate through each subfolder and the corresponding files
for subfolder, label in subfolders.items():
    # Prepare lists to store offered load and throughput values from the 10 directories
    offered_loads = []
    throughput_values = []

    for i in range(10):
        # Construct the path to the CSV file in each directory
        file_path = os.path.join(root_dir, f"memcached_repeats_{i}", subfolder, f"{subfolder}.csv")

        if os.path.exists(file_path):
            # Read the CSV file into a DataFrame
            df = pd.read_csv(file_path)

            # Append the offered load and throughput values to the lists
            offered_loads.append(df["offered_load"].values)
            throughput_values.append(df["throughput"].values)

    # Convert the lists to NumPy arrays for easy statistical calculations
    offered_loads = np.array(offered_loads)
    throughput_values = np.array(throughput_values)

    # Calculate mean and median across the 10 files for each index of the offered load and throughput
    for idx, desired_load in enumerate(desired_loads):
        # Extract offered_load and throughput values for the current index
        offered_load_for_idx = offered_loads[:, idx]
        throughput_for_idx = throughput_values[:, idx]

        # Calculate the mean and median for both offered_load and throughput
        offered_load_mean = np.mean(offered_load_for_idx)
        offered_load_median = np.median(offered_load_for_idx)
        throughput_mean = np.mean(throughput_for_idx)
        throughput_median = np.median(throughput_for_idx)
        throughput_min = np.min(throughput_for_idx)

        # Append the results to the DataFrame, including the subfolder type and the fixed "desired" offered load
        compiled_data = compiled_data.append({
            "subfolder_type": label,
            "desired": desired_load,
            "offered_load_mean": offered_load_mean,
            "offered_load_median": offered_load_median,
            "throughput_mean": throughput_mean,
            "throughput_median": throughput_median,
            "throughput_min": throughput_min
        }, ignore_index=True)

# Save the compiled results to a new CSV file
compiled_data.to_csv(output_csv, index=False)

print(f"Stats compiled and saved to {output_csv}")
