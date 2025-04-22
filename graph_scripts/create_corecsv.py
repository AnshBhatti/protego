#!/usr/bin/env python

import sys
import os
import pandas as pd
import numpy as np

pids = {}



def grab_pids():
    with open("PID.txt") as f:
        lines = f.readlines()
        for i in range(0, len(lines), 2):
            if "iokernel" not in lines[i]:
                pids[lines[i].rstrip()] = int(lines[i+1].rstrip())

            
def parse_kernel_log(process, pid):
    # note that I have it logging every 1000 us right now
    # if I split by whitespace, will the time in seconds be the second item?
    test = 1
    outfile = open("{}_cores.csv".format(process), "w")
    outfile.write("time(s),cores\n")

    with open("iokernel.node-0.log") as f:
        for line in f:
            if "PID" in line:
                line_items = line.split()
                time = float(line_items[2][:-1])
                curr_pid = int(line_items[7][:-1])
                active_cores = int(line_items[10][:-1])
                
                if curr_pid == pid:
                    outfile.write("{},{}\n".format(time, active_cores))

    outfile.close()



def main():
    # directory_name = sys.argv[1]
    grab_pids()
    for process, pid in pids.items():
        parse_kernel_log(process, pid)

if __name__ == '__main__':
    main()