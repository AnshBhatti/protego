import os
import sys
import shutil

if not os.path.exists("overall_csvs"):
    os.makedirs("overall_csvs")

for current_dir in os.listdir():
    if current_dir == "overall_csvs" or current_dir == "bw_timeseries_csvs" or not ("conns" in current_dir):
        continue
    os.chdir(current_dir)
    for f in os.listdir():
        if "breakwater" in f or "nocontrol" in f:
            # os.rename(f, current_dir + ".csv") # just here for when I mess up and need to rename the files better
            shutil.copy(f, "../overall_csvs/")
            print(f)
    os.chdir("..")
print("done")