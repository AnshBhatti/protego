import os
import pandas
import numpy as np
import glob
import csv


memcached = False
avg_service_time = 1
# [0.075]
if avg_service_time == 10:
    parking_scales = [0.4]
elif avg_service_time == 1:
    if memcached:
        parking_scales = [0.075]
    else:
        parking_scales = [0.2]
# parking_scales = 0.4 # [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]# [0.1, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
# [15]
core_credit_ratios = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]# [5, 10, 12, 14, 15, 16, 18, 20, 22, 24, 30]

if avg_service_time == 10:
    load = "600k" # doing ~600k or 700k for 10 us, what should it be for 1us? ~2 mil?
    ts_index = 5 # if just grabbing 600k and 700k timeseries, then this is 0 or 1. For 400k start, 2. For 100k start, 5
    overall_index = 5 # change this if it's a run where I started at 100k instead of 400k
elif avg_service_time == 1:
    load = "2000k"
    ts_index = 3  #  do 0 if just doing selected time series
    overall_index = 3 # 
    if memcached:
        load = "1500k"
        ts_index = 2
        overall_index = 2

vary_parking = True # if just using defaults, aka one parking scale and one core credit ratio, leave this option on, it's fine
# just make sure your list of parking scales is one element aka the one you're defaulting to.
vary_core_credit_ratio = False
using_all_schedulers = True # set to false when doing sensitivity, True for normal runs

# print out initial headers
schedulers = ["utilization"]# ["ias", "simple", "utilization", "delay_1.0_4.0", "delay_0.5_1.0"]
parking_schedulers = ["ias", "utilization"]# "simple"]
fields = []
if vary_parking:
    for s in parking_schedulers:
        for ps in parking_scales:
            fields.append(s + "_{}".format(ps))
elif vary_core_credit_ratio:
    for s in parking_schedulers:
        for ccr in core_credit_ratios:
            fields.append(s + "_{}".format(ccr))
if using_all_schedulers:
    fields += schedulers
fields.sort()
# print(fields)
csv_header = ",".join(fields) + "\n"

outfile = open("efficiency.csv", "w+")
outfile.write(csv_header)


# need to be in the combined_timeseries dir
os.chdir("bw_timeseries_csvs/combined_timeseries")

files = os.listdir()
files.sort()
print("make sure file order matches your effieciency.csv order!")
values = []
for f in files:
    if "spin" in f:
        continue
    # print(f)
    # continue
    pd = pandas.read_csv(f)
    val = pd.loc[ts_index, "avg_cores"]
    print(f + ": ", val)
    values.append("{:.4f}".format(val))
outfile.write(",".join(values) + "\n")

# needs to be in the overall csvs folder
os.chdir("../../overall_csvs")
directories = os.listdir()
directories.sort()

# single directory version, NON range load
# for dir in directories:
#     # print(dir)
#     # continue
#     if load in dir:
#         os.chdir(dir)
#         files = glob.glob("*{}*.csv".format(load))
#         for f in files:
#             p99 = pandas.read_csv(f)["p99"]
#             print(f + ":  {}".format(int(p99[0])))
#             # exit()
#         os.chdir("..")
# overall csvs version, RANGE LOADS
print("make sure file order matches your effieciency.csv order!")
values = []
for f in directories:
    if "spin" in f or not ".csv" in f:
        continue
    p99 = pandas.read_csv(f)["p99"]
    val = int(p99[overall_index])
    print(f + ":  {}".format(val))
    values.append("{}".format(val))
    # exit()
outfile.write(",".join(values) + "\n")