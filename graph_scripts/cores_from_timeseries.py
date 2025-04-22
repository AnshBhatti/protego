import os
import pandas
import numpy as np
import glob
import csv
import sys

metrics = ["timestamp", "num_cores", "credit_pool", "credit_used"]
fields = ["offered_load","avg_cores","avg_credit_pool","avg_credit_issued"]
field_string = "offered_load,avg_cores,avg_credit_pool,avg_credit_issued\n"
# if you change this, reflect it in csv header write as well

avg_service_time = 1 # check on ccr, haven't defaulted that yet
memcached = False

restricted_loads = False
# [0.05, 0.075, 0.1, 0.15, 0.2]
parking_scales = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
# [20]
core_credit_ratios = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]# [5, 10, 12, 14, 15, 16, 18, 20, 22, 24, 30]
default_parking_scale = 0.4
default_ccr = 15

default_ccr_on = True
default_parking_scale_on = True


if avg_service_time == 10:
    default_parking_scale = 0.4
elif avg_service_time == 1:
    if memcached:
        default_parking_scale = 0.075
    else:
        default_parking_scale = 0.2

conns = 100
nodes = 11

after_warmup_len = 4000000
output_dir = "combined_timeseries"

memcached_target = 25
if memcached:
    memcached_str = "_memcached"
else:
    memcached_str = ""

if avg_service_time == 10:
    if not restricted_loads:
        loads = ["100k", "200k", "300k", "400k", "500k", "600k", "700k", "800k", "900k", "1000k", "1100k", "1200k", "1300k", "1400k", "1600k", "2000k", "3000k"]# ["400k", "500k", "600k", "700k", "800k", "900k", "1000k", "1100k", "1200k", "1300k", "1400k", "1600k", "2000k", "3000k"]
        load_nums = [100000, 200000, 300000, 400000, 500000, 600000, 700000, 800000, 900000, 1000000, 1100000, 1200000, 1300000, 1400000, 1600000, 2000000, 3000000]
    else:
        loads = ["600k"]
        load_nums = [600000,]
    breakwater_target = 80
elif avg_service_time == 1:
    # 1 US
    if not restricted_loads:
        load_nums = [500000, 1000000, 1500000, 2000000, 2500000, 3000000, 3500000, 4000000, 4500000, 5000000, 5500000, 6000000, 6500000, 7000000]
        loads = ["500k", "1000k", "1500k", "2000k", "2500k", "3000k", "3500k", "4000k", "4500k", "5000k", "5500k", "6000k", "6500k", "7000k"]
    else:
        load_nums = [ 2000000, 2500000, 3000000, 3500000, 4000000]# [2000000]
        loads = ["2000k", "2500k", "3000k", "3500k", "4000k"] # ["2000k"]
    breakwater_target = 45
if memcached:
    breakwater_target = memcached_target
bw_thresh = breakwater_target * 2



def generate_csv(parking_scale, ccr, scheduler, parking_on):
    if parking_on and spinning:
        print("breakwater parking and spinning are enabled, are you sure about this?")
        exit()

    parking = "_park_{}_{}".format(parking_scale, ccr) if parking_on else ""
    spin = "_guaranteed_spinning" if spinning else ""

    files = []

    for l in loads:
        if len(sys.argv) > 1:
            print(os.getcwd())
            print("ts{}_breakwater_{}_{}{}_{}_*{}conns_{}nodes_{}{}.csv".format(memcached_str, breakwater_target, bw_thresh, spin, l, conns, nodes, scheduler, parking))
        f = glob.glob("ts{}_breakwater_{}_{}{}_{}_*{}conns_{}nodes_{}{}.csv".format(memcached_str, breakwater_target, bw_thresh, spin, l, conns, nodes, scheduler, parking))
        if len(f) > 1:
            print("too many files")
            for fname in f:
                print(f)
            exit()
        files.append(f[0])

    # for f in files:
    #     print(f)
    combined_data = []
    print("files like: " + files[0])
    for i,f in enumerate(files):
        # print(f)
        df = pandas.read_csv(f)
        Data = df[metrics]
        Data = np.array(Data)
        last_timestamp = Data[-1,0]
        mask = (Data[:,0] > (last_timestamp - after_warmup_len))
        Data = Data[mask,:] # remove rows that are during the warmup period
        combined_data.append((load_nums[i], np.average(Data[:,1]), np.average(Data[:,2]), np.average(Data[:,3]))) # avg of second col, which is cores

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if spinning:
        spin = "_" + spin
    outfile_name = "{}/combined_timeseries_{}_{}{}{}.csv".format(output_dir, breakwater_target, scheduler, parking, spin)
    if os.path.exists(outfile_name):
        print("error, file existed already: ")
        print(outfile_name)
    with open(outfile_name, "w+") as outfile:
        # csvwriter = csv.writer(outfile)
        # csvwriter.writerow(fields)
        outfile.write(field_string)
        for entry in combined_data:
            outfile.write("{:.4f},{:.4f},{:.4f},{:.4f}\n".format(entry[0], entry[1], entry[2], entry[3]))

# simple
# ias
# utilization_range_0.75_0.95
# delay_range_0.5_1.0
# delay_range_1.0_4.0
scheduler = "simple"
# parking_scale = 1.4
parking_on = True
spinning = False

if not parking_on:
    parking_scales = [0] # just make list 1 item long

if default_ccr_on:
    core_credit_ratios = [default_ccr]
if default_parking_scale_on or spinning:
    parking_scales = [default_parking_scale]

schedulers = ["utilization_range_0.75_0.95",] #"ias", "simple", "delay_range_1.0_4.0", "delay_range_0.5_1.0"]
parking_schedulers = ["ias", "utilization_range_0.75_0.95", ] # "simple"]

parking_on = True
for s in parking_schedulers:
    for ccr in core_credit_ratios:
        for ps in parking_scales:
            generate_csv(ps, ccr, s, True)
            # exit()

for s in schedulers:
    generate_csv(0, 0, s, False)

spinning = True
generate_csv(0, 0, "simple", False)

