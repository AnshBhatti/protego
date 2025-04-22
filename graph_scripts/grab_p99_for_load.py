import os
import pandas
import numpy as np
import glob
import csv

load = "600k"
index = 2 # this reflects 600k being the third row for overall csvs. 
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
for f in directories:
    p99 = pandas.read_csv(f)["p99"]
    print(f + ":  {}".format(int(p99[index])))
    # exit()
