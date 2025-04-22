import os
import sys
import shutil
import csv


middle_text = "500k" # make this 400k or 100k for 10 us, 500k for 1 us Or really just the "first load" we do in general

if not os.path.exists("bw_timeseries_csvs"):
    os.makedirs("bw_timeseries_csvs")
for current_dir in os.listdir():
    if current_dir == "overall_csvs" or current_dir == "bw_timeseries_csvs" or not ("conns" in current_dir):
        continue
    os.chdir(current_dir)
    for f in os.listdir():
        if "timeseries" in f: # and ("600k" in f or "700k" in f): # remove this RHS if doing individual runs, but I don't think I'll readopt that idea
            load_txt = f.split("_")[0]
            file_name = current_dir.replace(middle_text, load_txt)
            
            # os.symlink(f, "../bw_timeseries_csvs/ts_{}".format(file_name + ".csv"))
            shutil.copy(f, "../bw_timeseries_csvs/ts_{}".format(file_name + ".csv"))
            print(file_name)
    os.chdir("..")
    # exit()
print("done")
