import os
import pandas
import numpy as np
import glob
import csv

load = "600k"
index = 1 # because this will change easily... and I don't think I can grab a row so easily, since it's dictated by a floating value


files = os.listdir()
files.sort()

for f in files:
    # print(f)
    # continue
    pd = pandas.read_csv(f)
    # print(pd)
    print(f + ": ", pd.loc[index, "avg_cores"])