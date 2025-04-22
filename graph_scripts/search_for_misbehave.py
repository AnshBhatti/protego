import os
import pandas
import numpy as np
import glob
import csv


def loop_dirs():
    directory_starter_name = "shenango_repeats_"
    directories = os.listdir()
    directories.sort()
    loads = []

    for dir in directories:
        if not directory_starter_name in dir:
            continue
        os.chdir(dir)
        for subdir in os.listdir():
            os.chdir(subdir)
            search_single_run_dir(subdir)
            os.chdir("..")
        print(dir)
        os.chdir("..")

def search_single_run_dir(dir, scale=0.9,):
    for f in os.listdir():
        if "breakwater" in f:
            reported_throughput = float(pandas.read_csv(f)["throughput"][0])

    for f in os.listdir():
        if "_timeseries" in f:
            df = pandas.read_csv(f)
            start_time = int(df["timestamp"][0])
            print(reported_throughput)
            print(start_time)
            exit()

loop_dirs()

