import os
import pandas
import numpy as np
import glob
import csv
import sys


parking_scales = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]# [0.1, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
core_credit_ratios = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]# [5, 10, 12, 14, 15, 16, 18, 20, 22, 24, 30]

avg_service_time = 10
vary_parking = False
vary_core_credit_ratio = True
scheduler = "simple"

if avg_service_time == 10:
    load = "1100k" # doing ~600k or 700k for 10 us, what should it be for 1us? ~2 mil?
    # ts_index = 2 # because this will change easily... and I don't think I can grab a row so easily, since it's dictated by a floating value
    overall_index = 9 # 8 for 1.2 mil?
elif avg_service_time == 1:
    load = "3500k"
    # ts_index = 3
    overall_index = 6 # 7 for 4 mil? 6 for 3.5 mil

if vary_parking:
    csv_header = "parking_scale,p99\n"
    name = "ps"
else:
    csv_header = "core_credit_ratio,p99\n"
    name = "ccr"

outfile = open("sensivity_p99_{}_{}.csv".format(name, scheduler), "w+")
outfile.write(csv_header)


# needs to be in the overall csvs folder
os.chdir("overall_csvs")
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
if vary_parking:
    for ps in parking_scales:
        # print("*{}_park_{}*.csv".format(s, ps))
        f = glob.glob("*{}_park_{}*.csv".format(scheduler, ps))[0]
        p99 = pandas.read_csv(f)["p99"]
        val = int(p99[overall_index])
        outfile.write("{},{}\n".format(ps, val))
else:
    for ccr in core_credit_ratios:
        f = glob.glob("*{}_park*{}*.csv".format(scheduler, ccr))[0]
        p99 = pandas.read_csv(f)["p99"]
        val = int(p99[overall_index])
        outfile.write("{},{}\n".format(ccr, val))
print("done. produced file: {}".format("sensivity_p99_{}_{}.csv".format(name, scheduler)))