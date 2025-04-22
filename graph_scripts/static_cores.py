import os
import sys
import shutil
import pandas

if not os.path.exists("overall_csvs"):
    os.makedirs("overall_csvs")

data = []
metrics = ["p99"]
avg_service_time = 1
memcached = True
if avg_service_time == 10:
    load = "600k" # or 700k
elif avg_service_time == 1:
    load = "2000k"
    if memcached:
        load = "1500k"

for current_dir in os.listdir():
    if current_dir == "overall_csvs" or current_dir == "bw_timeseries_csvs" or not ("conns" in current_dir):
        continue
    os.chdir(current_dir)
    for f in os.listdir():
        if ("breakwater" in f or "nocontrol" in f) and load in f:
            splits = f.split("_")
            for s in splits:
                if "cores" in s:
                    num_cores = int(s[:-5])
            cores = f.split("_")
            pd = pandas.read_csv(f)
            data.append((num_cores, pd["p99"][0]))
    os.chdir("..")
print(data)

print("done")