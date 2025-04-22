import os
import sys
import shutil
import re
import csv

swaptions = True
swaptions_start = 4.5
swaptions_end = 4.5 + 8

def calculate_average_swaptions(filename):
    count = 0
    with open(filename, 'r') as file:
        for line in file:
            if "detected" in line:
                continue
            splits = line.split()
            curr_time = splits[1]
            curr_time = float(curr_time[:-1])
            if curr_time < swaptions_start:
                continue
            if curr_time > swaptions_end:
                break
            # print(splits[-2])
            count += int(splits[-2])
    return count / (swaptions_end - swaptions_start) # give per second rate


def calculate_average(filename):
    # Regular expression to match the lines of interest
    pattern = re.compile(r"\[\s*\d+\.\d+\] CPU \d+\| <\d> \d+\.\d+,\d+\.\d+")
    
    total = 0
    count = 0

    start = 5
    
    with open(filename, 'r') as file:
        for line in file:
            # Find matching lines
            match = pattern.search(line)
            if match:
                count += 1
                if count < start:
                    continue
                # Extract the last number after the comma
                last_number = float(line.strip().split(',')[-1])
                total += last_number
                
                # Stop after the first 8 entries
                if count - start >= 8:
                    break
    
    # Calculate and print the average
    if count > 0:
        average = total / 8
        if count != start + 8:
            print(f"had {count} entries, average: {average:.6f}")
        return average
    else:
        print("No matching entries found in the file.")
        return 0


## essentially main
headers = ["offered_load", "background_ops"]
for current_dir in os.listdir():
    if "spinning" in current_dir or current_dir == "overall_csvs" or current_dir == "bw_timeseries_csvs" or not ("conns" in current_dir):
        continue
    print("\nin directory: {}\n".format(current_dir))
    os.chdir(current_dir)
    if "antagonist" not in os.listdir():
        print("couldn't find antagonist directory")
        exit()
    os.chdir("antagonist")
    values = []
    for f in os.listdir():
        load = int(f.split("k")[0])
        if swaptions:
            avg = calculate_average_swaptions(f)
        else:
            avg = calculate_average(f)
        values.append([load, avg])
    
    filename = "../antagonist_data.csv"
    values.sort() # sorts by first element

    # Write data to CSV
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        # Write headers
        writer.writerow(headers)
        # Write each row of data
        writer.writerows(values)
    os.chdir("../..")


### move these antagonist csvs into one spot, like overall_csv gather
if not os.path.exists("antagonist_csvs"):
    os.makedirs("antagonist_csvs")

for current_dir in os.listdir():
    if "spinning" in current_dir or current_dir == "overall_csvs" or current_dir == "bw_timeseries_csvs" or not ("conns" in current_dir):
        continue
    os.chdir(current_dir)
    for f in os.listdir():
        if "antagonist_data.csv" == f:
            # os.rename(f, current_dir + ".csv") # just here for when I mess up and need to rename the files better
            shutil.copy(f, "../antagonist_csvs/{}".format(current_dir + "_antagonist.csv"))
            print(f)
    os.chdir("..")


