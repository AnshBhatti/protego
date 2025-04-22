#!/usr/bin/env python3

import paramiko
import os
from time import sleep
from util import *
import config_remote
from datetime import datetime
import random

service_time = 10 # make sure the right loads are being done in param synthetic
conns = [100]
if service_time == 10:
    loads = [100000, 200000, 300000, 400000, 500000, 600000, 700000, 800000, 900000, 1000000, 1100000, 1200000, 1300000, 1400000, 1600000, 2000000, 3000000]
    breakwater_target = 80 # reccomended for 1 us service time and 10 us rtt
    breakwater_targets = [80]
    # breakwater_targets = [80, 60, 40]
    slo = 200
elif service_time == 1:
    loads = [500000, 1000000, 1500000, 2000000, 2500000, 3000000, 3500000, 4000000, 4500000, 5000000, 5500000, 6000000, 6500000, 7000000]
    breakwater_target = 45 # reccomended for 1 us service time and 10 us rtt
    breakwater_targets = [45]
    slo = 110
algorithms = ["breakwater"]
schedulers = ["ias", "simple"] # 
delay_ranges = [[0.5, 1], [1, 4]]
utilization_ranges = [[0.75, 0.95]]
load_factors = [0.3, 0.7]
# load_factors = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0] # going to do one additional run before running this where BREAKWATER_CORE_PARKING is off.
# load_factors = [0.2, 0.8] # going to do one additional run before running this where BREAKWATER_CORE_PARKING is off.
ccr_values = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
# ccr_values = [11]
# need to do individual load runs in order to grab the timeseries each time.
# uncertain of the best way to do this besides looping over loads AND over these loadfactors- will probably take forever

algorithm = "breakwater"
scheduler = "simple"  # make it ias later (which is caladan)
connections = 100


service_distribution = "exp"  # make it bimod after
offered_load = 850000
range_loads = 1 # can comment out in code to use the multiple same load behavior
loadshift = 0
spin_server = 0
num_cores_server = 18
num_cores_lc = 16
num_cores_lc_guaranteed = 0
num_cores_antagonist_guaranteed = 0
caladan_threshold = 10
count = 1

caladan_interval = 10

sched_delay = 0
sched_utilization = 0
delay_lower = 0.5
delay_upper = 1.0
utilization_lower = 0.75
utilization_upper = 0.95

# 1 is true, 0 is false
avoid_large_downloads = 1
download_all_tasks = 0
breakwater_parking = 1
breakwater_timeseries = 1

current_load_factor = 1.0
core_credit_ratio = 12

specified_experiment_name = "None"

antagonist = 0

# rebuild is needed if any changes require recomplilation, ex. timeseries involves changing
# bw_server.c, so recompilation is needed. Can do it for first run, then turn off usually unless changing target delay, etc.
rebuild = 1

script_name = "param_memcached_antagonist.py"

def call_experiment():
    global count
    print("experiment number: {}".format(count))
    # if count < 2:
    #     count += 1
    #     return
    count += 1
    # return
    # return
    # 5 per line
    failure_code = os.system("python3 -u {}"\
              " {} {:d} {:d} {:d} {}"\
              " {:d} {:d} {:d} {:d} {:d}"\
              " {:d} {:d} {:d} {:d} {:d}"\
              " {} {:d} {:f} {:f} {:d}"\
              " {:f} {:f} {:f} {:d} {}"\
              " {:d} {:d} {:d} {:d} {}"\
              " {:d} {:d}".format(script_name,
              algorithm, connections, service_time, breakwater_target, service_distribution,
              offered_load, loadshift, spin_server, num_cores_server, num_cores_lc,
              num_cores_lc_guaranteed, caladan_threshold, slo, avoid_large_downloads, range_loads,
              scheduler, sched_delay, delay_lower, delay_upper, sched_utilization,
              utilization_lower, utilization_upper, current_load_factor, caladan_interval, breakwater_parking,
              core_credit_ratio, download_all_tasks, breakwater_timeseries, rebuild, specified_experiment_name,
              antagonist, num_cores_antagonist_guaranteed))
    if failure_code != 0:
        print("sys call failed, look at console or log")
        exit()
    print("algorithm: {}".format(algorithm))
    print("spinning: {}\nscheduler: {}\nsched_delay: {}".format(spin_server, scheduler, sched_delay))
    print("bw target: {}\ndelay_lower: {}\nutilization_lower {}".format(breakwater_target, delay_lower, utilization_lower))
    print("breakwater parking: {}, load factor: {}, core credit: {}\n".format(breakwater_parking, current_load_factor, core_credit_ratio))
    print("sleeping for 5 seconds before next connection\n\n")
    sleep(5)
    # just for testing
    # exit()

def vary_parking_and_efficiency_plot():
    global algorithm
    global connections
    global service_time
    global breakwater_target
    global service_distribution
    global offered_load
    global loadshift
    global spin_server
    global num_cores_server
    global num_cores_lc
    global num_cores_lc_guaranteed
    global caladan_threshold
    global slo
    global scheduler
    global delay_ranges
    global utilization_ranges
    global caladan_interval
    global delay_lower
    global delay_upper
    global utilization_lower
    global utilization_upper
    global sched_delay
    global sched_utilization
    global current_load_factor
    global breakwater_parking
    global core_credit_ratio

    global range_loads

    # TODO maybe re run these, and grab EVERY timeseries just for records sake.
    # MAKE SURE to set rebuild to true in the param file for the first run at least.
    # quick range loads for just ias and simple parking
    
    service_time = 10
    breakwater_target = 80
    slo = 200
    core_credit_ratio = 15
    breakwater_parking = 1
    spin_server = 0
    for lf in load_factors:
        current_load_factor = lf
        for s in schedulers:
            scheduler = s
            call_experiment()
    breakwater_parking = 0

    service_time = 1
    breakwater_target = 45
    slo = 110
    core_credit_ratio = 15
    breakwater_parking = 1
    spin_server = 0
    for lf in load_factors:
        current_load_factor = lf
        for s in schedulers:
            scheduler = s
            call_experiment()
    breakwater_parking = 0

    # spin run
    # for s in schedulers:
    #     scheduler = s
    #     call_experiment()
    # spin_server = 1
    # scheduler = "simple"
    # num_cores_lc_guaranteed = 16
    # call_experiment()
    # spin_server = 0
    # num_cores_lc_guaranteed = 0

    # # do utilization range and delay range calls here
    # breakwater_parking = 0
    # scheduler = "range_policy"
    # caladan_interval = 5
    # for range_s in ["utilization", "delay"]:
    #     breakwater_parking = 0
    #     if range_s == "delay":
    #         for d in delay_ranges:
    #             delay_lower = d[0]
    #             delay_upper = d[1]
    #             sched_delay = 1
    #             call_experiment()
    #             sched_delay = 0
    #     elif range_s == "utilization":
    #         for u in utilization_ranges:
    #             utilization_lower = u[0]
    #             utilization_upper = u[1]
    #             sched_utilization = 1
    #             call_experiment()
    #             sched_utilization = 0

    # static curve, varying cores. turn off range loads before running (FOR 1 us, figure out what "half capacity" should be)
    # range_loads = 0
    # breakwater_parking = 0
    # offered_load = 600000
    # spin_server = 1
    # scheduler = "simple"
    # half load for 1 us is 2000000, for 10 us it's either 600000 or 700000 but we've been going with 600000
    # for l in [2000000]: # [600000, 700000]:
    #     offered_load = l
    #     for cores in [1, 2, 3, 4,5,6,7,8,9,10,11,12,13,14,15,16]:
    #         num_cores_server = cores
    #         num_cores_lc = cores
    #         num_cores_lc_guaranteed = cores
    #         call_experiment()
def vary_targets():
    global algorithm
    global connections
    global service_time
    global breakwater_target
    global service_distribution
    global offered_load
    global loadshift
    global spin_server
    global num_cores_server
    global num_cores_lc
    global num_cores_lc_guaranteed
    global caladan_threshold
    global slo
    global scheduler
    global delay_ranges
    global utilization_ranges
    global caladan_interval
    global delay_lower
    global delay_upper
    global utilization_lower
    global utilization_upper
    global sched_delay
    global sched_utilization
    global current_load_factor
    global breakwater_parking
    global core_credit_ratio

    global range_loads
    
    range_loads = 1
    breakwater_parking = 0
    # spin_server = 1
    # num_cores_lc_guaranteed = 16
    # scheduler = "simple"
    # breakwater_target = 80
    # service_time = 10
    # call_experiment()
    # spin_server = 0
    # num_cores_lc_guaranteed = 0

    schedulers = ["range_policy"] # "ias"]
    for s in schedulers:
        scheduler = s
        for t in [80, 60, 40]:
            breakwater_target = t
            if s == "range_policy":
                caladan_interval = 5
                sched_utilization = 1
                call_experiment()
                sched_utilization = 0
                caladan_interval = 10
            else:
                call_experiment()

def baselines():
    global algorithm
    global connections
    global service_time
    global breakwater_target
    global service_distribution
    global offered_load
    global loadshift
    global spin_server
    global num_cores_server
    global num_cores_lc
    global num_cores_lc_guaranteed
    global caladan_threshold
    global slo
    global scheduler
    global delay_ranges
    global utilization_ranges
    global caladan_interval
    global delay_lower
    global delay_upper
    global utilization_lower
    global utilization_upper
    global sched_delay
    global sched_utilization
    global current_load_factor
    global breakwater_parking
    global core_credit_ratio

    global range_loads

    range_loads = 1
    breakwater_parking = 0

    for st in [10]:
        service_time = st
        for s in ["ias", "simple", "range_policy", "spin"]:
            scheduler = s
            if s == "range_policy":
                caladan_interval = 5
                for range_s in ["delay", "utilization"]: # "utilization",  ran this
                    if range_s == "delay":
                        for d in delay_ranges:
                            delay_lower = d[0]
                            delay_upper = d[1]
                            sched_delay = 1
                            call_experiment()
                            sched_delay = 0
                    elif range_s == "utilization":
                        for u in utilization_ranges:
                            utilization_lower = u[0]
                            utilization_upper = u[1]
                            sched_utilization = 1
                            call_experiment()
                            sched_utilization = 0
                caladan_interval = 10
            elif s == "spin":
                scheduler = "simple"
                spin_server = 1
                num_cores_lc_guaranteed = 16
                call_experiment()
                spin_server = 0
                num_cores_lc_guaranteed = 0
            elif s == "simple":
                caladan_interval = 5
                caladan_threshold = 5
                for i in range(2):
                    call_experiment()
                caladan_interval = 10
                caladan_threshold = 10
            else:
                caladan_interval = 10
                call_experiment()
    caladan_interval = 10
    breakwater_parking = 1
    current_load_factor = 0.4
    core_credit_ratio = 15
    for s in ["ias", "simple"]:
        scheduler = s
        if scheduler == "ias":
            for i in range(5):
                call_experiment()
        else:
            call_experiment()

#### good to use this one 
def figure_1_4_5_6_7_11(arg_service_time=10, memcached_target=25):
    global algorithm
    global connections
    global service_time
    global breakwater_target
    global service_distribution
    global offered_load
    global loadshift
    global spin_server
    global num_cores_server
    global num_cores_lc
    global num_cores_lc_guaranteed
    global caladan_threshold
    global slo
    global scheduler
    global delay_ranges
    global utilization_ranges
    global caladan_interval
    global delay_lower
    global delay_upper
    global utilization_lower
    global utilization_upper
    global sched_delay
    global sched_utilization
    global current_load_factor # using this for parking scale
    global breakwater_parking
    global core_credit_ratio

    global range_loads
    global avoid_large_downloads
    global download_all_tasks
    global breakwater_timeseries
    global specified_experiment_name
    global script_name
    global rebuild

    download_all_tasks = 0
    breakwater_timeseries = 1 # for now, with 4 nodes
    rebuild = 1
    range_loads = 1

    # TODO maybe re run these, and grab EVERY timeseries just for records sake.
    # MAKE SURE to set rebuild to true in the param file for the first run at least.
    # quick range loads for just ias and simple parking
    # st time of 0 is for memcached
    if arg_service_time == 10:
        service_time = 10
        breakwater_target = 80
        slo = 200
        current_load_factor = 0.4
    elif arg_service_time == 1:
        service_time = 1
        breakwater_target = 45
        slo = 110
        current_load_factor = 0.2
    elif arg_service_time == 0: ### memcached
        service_time = 1 # important to set to 1 to get right offered loads and time series
        breakwater_target = memcached_target # making this a param
        slo = 50 if memcached_target == 25 else 110
        current_load_factor = 0.2 # this is a guess
        script_name = "param_memcached_antagonist.py"

    else:
        print("invalid service time")
        return
    # spin run
    breakwater_parking = 0
    caladan_interval = 10
    caladan_threshold = 10
    spin_server = 1
    scheduler = "simple"
    num_cores_lc_guaranteed = 16
    call_experiment()
    spin_server = 0
    num_cores_lc_guaranteed = 0
    # return
    # the two schedulers that coresync works with
    # core_credit_ratio = 30
    breakwater_parking = 1 # enable coresync
    spin_server = 0
    parking_scales_temp = [0.075]
    if arg_service_time != 0:
        parking_scales_temp = [current_load_factor]
    
    for ps in parking_scales_temp: # let's test some parking scales
        current_load_factor = ps
        for s in ["ias",]:# "simple"]:
            caladan_interval = 10
            caladan_threshold = 10
            scheduler = s
            call_experiment()
    breakwater_parking = 0

    # do utilization range and delay range calls here
    # for ps in parking_scales_temp:# [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]:
        # current_load_factor = ps
    breakwater_parking = 0
    scheduler = "range_policy"
    caladan_interval = 5
    for range_s in ["utilization", "delay"]:
        breakwater_parking = 0
        if range_s == "delay":
            for d in delay_ranges:
                delay_lower = d[0]
                delay_upper = d[1]
                sched_delay = 1
                call_experiment()
                sched_delay = 0
        elif range_s == "utilization":
            for u in utilization_ranges:
                breakwater_parking = 1
                utilization_lower = u[0]
                utilization_upper = u[1]
                sched_utilization = 1
                call_experiment() # utilization range with coresync run
                sched_utilization = 0
                breakwater_parking = 0
                utilization_lower = u[0]
                utilization_upper = u[1]
                sched_utilization = 1
                call_experiment() # normal run
                sched_utilization = 0
                # exit() # temp TODO just want to run the util run
    # return
    # non coresync shenango and caladan runs?
    for s in ["ias","simple"]:
        if s == "simple":
            caladan_interval = 5
            caladan_threshold = 5
        else:
            caladan_interval = 10
            caladan_threshold = 10
        scheduler = s
        call_experiment()
    return
    # spin run
    caladan_interval = 10
    caladan_threshold = 10
    spin_server = 1
    scheduler = "simple"
    num_cores_lc_guaranteed = 16
    call_experiment()
    spin_server = 0
    num_cores_lc_guaranteed = 0
    # return
    # static curve, varying cores. turn off range loads before running (FOR 1 us, figure out what "half capacity" should be)
    range_loads = 0
    breakwater_parking = 0
    # offered_load = 600000
    spin_server = 1
    scheduler = "simple"
    # half load for 1 us is 2000000, for 10 us it's either 600000 or 700000 but we've been going with 600000
    half_loads = []
    if service_time == 1:
        if arg_service_time == 0:
            half_loads = [1500000]
        else:
            half_loads = [2000000]
    elif service_time == 10:
        half_loads = [600000, 700000]

    for l in half_loads:
        offered_load = l
        for cores in [1, 2, 3, 4,5,6,7,8,9,10,11,12,13,14,15,16]:
            num_cores_server = cores
            num_cores_lc = cores
            num_cores_lc_guaranteed = cores
            call_experiment()

def sensitivity(arg_service_time=10, memcached_target=25):
    global algorithm
    global connections
    global service_time
    global breakwater_target
    global service_distribution
    global offered_load
    global loadshift
    global spin_server
    global num_cores_server
    global num_cores_lc
    global num_cores_lc_guaranteed
    global caladan_threshold
    global slo
    global scheduler
    global delay_ranges
    global utilization_ranges
    global caladan_interval
    global delay_lower
    global delay_upper
    global utilization_lower
    global utilization_upper
    global sched_delay
    global sched_utilization
    global current_load_factor # using this for parking scale
    global breakwater_parking
    global core_credit_ratio

    global range_loads
    global avoid_large_downloads
    global download_all_tasks
    global breakwater_timeseries
    global specified_experiment_name
    global script_name
    global rebuild

    download_all_tasks = 0
    breakwater_timeseries = 1 # for now, with 4 nodes
    rebuild = 1
    range_loads = 0

    # TODO maybe re run these, and grab EVERY timeseries just for records sake.
    # MAKE SURE to set rebuild to true in the param file for the first run at least.
    # quick range loads for just ias and simple parking
    # st time of 0 is for memcached
    if arg_service_time == 10:
        service_time = 10
        breakwater_target = 80
        slo = 200
        current_load_factor = 0.4
        offered_load = 600000
    elif arg_service_time == 1:
        service_time = 1
        breakwater_target = 45
        slo = 110
        current_load_factor = 0.2
    elif arg_service_time == 0: ### memcached
        service_time = 1 # important to set to 1 to get right offered loads and time series
        breakwater_target = memcached_target # making this a param
        slo = 50 if memcached_target == 25 else 110
        current_load_factor = 0.2 # this is a guess
        script_name = "param_memcached_antagonist.py"

    else:
        print("invalid service time")
        return
    # the two schedulers that coresync works with
    core_credit_ratio = 15
    breakwater_parking = 1 # enable coresync
    spin_server = 0
    # parking_scales_temp = [0.075, 0.05, 0.1, 0.15, 0.2]
    parking_scales_temp = [0.1, 0.2] # [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    core_credit_ratios = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20] # [5, 10, 12, 14, 15, 16, 18, 20, 22, 24, 30]
    param_sensitivity = True
    if arg_service_time != 0 and not param_sensitivity:
        parking_scales_temp = [current_load_factor]
    
    for ps in parking_scales_temp: # let's test some parking scales
        current_load_factor = ps
        for s in ["ias", "simple"]:
            caladan_interval = 10
            caladan_threshold = 10
            scheduler = s
            call_experiment()
    current_load_factor = 0.4
    for ccr in core_credit_ratios: # let's test some parking scales
        if ccr == 15:
            continue
        core_credit_ratio = ccr
        for s in ["ias", "simple"]:
            caladan_interval = 10
            caladan_threshold = 10
            scheduler = s
            # call_experiment()
    breakwater_parking = 0

def repeats(count, arg_service_time=10, memcached_target=25):
    global algorithm
    global connections
    global service_time
    global breakwater_target
    global service_distribution
    global offered_load
    global loadshift
    global spin_server
    global num_cores_server
    global num_cores_lc
    global num_cores_lc_guaranteed
    global caladan_threshold
    global slo
    global scheduler
    global delay_ranges
    global utilization_ranges
    global caladan_interval
    global delay_lower
    global delay_upper
    global utilization_lower
    global utilization_upper
    global sched_delay
    global sched_utilization
    global current_load_factor # using this for parking scale
    global breakwater_parking
    global core_credit_ratio

    global range_loads
    global avoid_large_downloads
    global download_all_tasks
    global breakwater_timeseries
    global specified_experiment_name
    global script_name
    global rebuild
    specified_experiment_name = "memcached_repeats_{}".format(count)
    download_all_tasks = 0
    breakwater_timeseries = 1
    rebuild = 1
    range_loads = 1

    # TODO maybe re run these, and grab EVERY timeseries just for records sake.
    # MAKE SURE to set rebuild to true in the param file for the first run at least.
    # quick range loads for just ias and simple parking
    # st time of 0 is for memcached
    if arg_service_time == 10:
        service_time = 10
        breakwater_target = 80
        slo = 200
        current_load_factor = 0.4
    elif arg_service_time == 1:
        service_time = 1
        breakwater_target = 45
        slo = 110
        current_load_factor = 0.2
    elif arg_service_time == 0: ### memcached
        service_time = 1 # important to set to 1 to get right offered loads and time series
        breakwater_target = memcached_target # making this a param
        slo = 50 if memcached_target == 25 else 110
        current_load_factor = 0.075 # this is a guess
        script_name = "param_memcached_antagonist.py"

    else:
        print("invalid service time")
        return
    # the two schedulers that coresync works with
    core_credit_ratio = 15
    breakwater_parking = 1 # enable coresync
    spin_server = 0
    # for ps in [0.4]: # let's test some parking scales
    #     current_load_factor = ps
    for s in ["ias", ]: # "simple"
        caladan_interval = 10
        caladan_threshold = 10
        scheduler = s
        call_experiment()
    breakwater_parking = 0
    # non coresync shenango and caladan runs?
    for s in ["ias","simple"]:
        if s == "simple":
            caladan_interval = 5
            caladan_threshold = 5
        else:
            caladan_interval = 10
            caladan_threshold = 10
        scheduler = s
        call_experiment()
    breakwater_parking = 0
    scheduler = "range_policy"
    caladan_interval = 5
    # just util
    for range_s in ["utilization"]: 
        breakwater_parking = 0
        if range_s == "delay":
            for d in delay_ranges:
                delay_lower = d[0]
                delay_upper = d[1]
                sched_delay = 1
                call_experiment()
                sched_delay = 0
        elif range_s == "utilization":
            for u in utilization_ranges:
                utilization_lower = u[0]
                utilization_upper = u[1]
                sched_utilization = 1
                call_experiment()
                sched_utilization = 0
                # exit() # temp TODO just want to run the util run
    # spin run
    caladan_interval = 10
    caladan_threshold = 10
    spin_server = 1
    scheduler = "simple"
    num_cores_lc_guaranteed = 16
    call_experiment()
    spin_server = 0
    num_cores_lc_guaranteed = 0

def shenango_misbehave():
    global algorithm
    global connections
    global service_time
    global breakwater_target
    global service_distribution
    global offered_load
    global loadshift
    global spin_server
    global num_cores_server
    global num_cores_lc
    global num_cores_lc_guaranteed
    global caladan_threshold
    global slo
    global scheduler
    global delay_ranges
    global utilization_ranges
    global caladan_interval
    global delay_lower
    global delay_upper
    global utilization_lower
    global utilization_upper
    global sched_delay
    global sched_utilization
    global current_load_factor
    global breakwater_parking
    global core_credit_ratio

    global range_loads
    global avoid_large_downloads
    global download_all_tasks
    global breakwater_timeseries
    global specified_experiment_name
    global rebuild

    

    range_loads = 0 # we will do them ourselves
    avoid_large_downloads = 0 #  we want tasks?
    download_all_tasks = 0
    breakwater_timeseries = 1
    rebuild = 0 # stop rebuilding after first run

    breakwater_parking = 0
    spin_server = 0
    scheduler = "simple"
    caladan_interval = 5
    caladan_threshold = 5

    run_count = 0
    has_built = False
    for run in range(10, 30):
        specified_experiment_name = "shenango_repeats_{}".format(run)
        for l in [600000, 700000, 800000]:
            if not has_built:
                rebuild = 1
                has_built = True
            else:
                rebuild = 0
            offered_load = l
            call_experiment()
            run_count += 1
    
    # spin_server = 1
    # num_cores_lc_guaranteed = 16
    # breakwater_parking = 0
    # for l in loads:
    #     offered_load = l
    #     call_experiment()
    #     run_count += 1

def test_memcached():
    global algorithm
    global connections
    global service_time
    global breakwater_target
    global service_distribution
    global offered_load
    global loadshift
    global spin_server
    global num_cores_server
    global num_cores_lc
    global num_cores_lc_guaranteed
    global caladan_threshold
    global slo
    global scheduler
    global delay_ranges
    global utilization_ranges
    global caladan_interval
    global delay_lower
    global delay_upper
    global utilization_lower
    global utilization_upper
    global sched_delay
    global sched_utilization
    global current_load_factor
    global breakwater_parking
    global core_credit_ratio

    global range_loads
    global avoid_large_downloads
    global download_all_tasks
    global breakwater_timeseries
    global specified_experiment_name
    global script_name
    global rebuild

    script_name = "param_memcached_antagonist.py"

    range_loads = 1
    avoid_large_downloads = 0
    download_all_tasks = 0
    breakwater_timeseries = 1
    rebuild = 1

    breakwater_parking = 0
    spin_server = 0
    scheduler = "simple"
    caladan_interval = 5
    caladan_threshold = 5

    service_time = 1 # required to get the right loads
    # inho says 25... we'll see
    breakwater_target = 25
    slo = 50
    breakwater_timeseries = 1

    call_experiment()

#### good to use this one
def testing_antagonist_nov2024(arg_service_time=10, memcached_target=25):
    global algorithm
    global connections
    global service_time
    global breakwater_target
    global service_distribution
    global offered_load
    global loadshift
    global spin_server
    global num_cores_server
    global num_cores_lc
    global num_cores_lc_guaranteed
    global caladan_threshold
    global slo
    global scheduler
    global delay_ranges
    global utilization_ranges
    global caladan_interval
    global delay_lower
    global delay_upper
    global utilization_lower
    global utilization_upper
    global sched_delay
    global sched_utilization
    global current_load_factor # using this for parking scale
    global breakwater_parking
    global core_credit_ratio

    global range_loads
    global avoid_large_downloads
    global download_all_tasks
    global breakwater_timeseries
    global specified_experiment_name
    global script_name
    global rebuild
    global antagonist
    global num_cores_antagonist_guaranteed

    # TODO maybe re run these, and grab EVERY timeseries just for records sake.
    # MAKE SURE to set rebuild to true in the param file for the first run at least.
    # quick range loads for just ias and simple parking
    # st time of 0 is for memcached
    if arg_service_time == 10:
        service_time = 10
        breakwater_target = 80
        slo = 200
        current_load_factor = 0.4
    elif arg_service_time == 1:
        service_time = 1
        breakwater_target = 45
        slo = 110
        current_load_factor = 0.2
    elif arg_service_time == 0: ### memcached
        service_time = 1 # important to set to 1 to get right offered loads and time series
        breakwater_target = memcached_target # making this a param
        slo = 50 if memcached_target == 25 else 110
        current_load_factor = 0.075 # this is a guess
        script_name = "param_memcached_antagonist.py"

    else:
        print("invalid service time")
        return
    
    download_all_tasks = 0
    breakwater_timeseries = 1 # for now, with 4 nodes
    rebuild = 1
    range_loads = 1
    antagonist = 1
    # leaving 2 for the timer
    num_cores_server = 18 # but, they don't leave any for timer with swaptions. Could see how 18 plays out
    num_cores_lc = 18
    num_cores_lc_guaranteed = 18 # TODO seems to be needed
    num_cores_antagonist_guaranteed = 0
    current_load_factor = 0.075
    core_credit_ratio = 15
    algorithm = "nocontrol"

    breakwater_parking = 0
    spin_server = 0
    
    # for temp_load in range(500000, 4000001, 500000): # [500000]:
    # offered_load = temp_load
    # coresync run
    breakwater_parking = 1 # enable coresync
    spin_server = 0
    
    for ps in [current_load_factor]: # let's test some parking scales
        current_load_factor = ps
        for s in ["ias",]:# "simple"]:
            caladan_interval = 10
            caladan_threshold = 10
            scheduler = s
            call_experiment()
    # return
    breakwater_parking = 0
    # do utilization range and delay range calls here
    breakwater_parking = 0
    scheduler = "range_policy"
    caladan_interval = 5
    for range_s in ["utilization", "delay"]:
        breakwater_parking = 0
        if range_s == "delay":
            for d in delay_ranges:
                delay_lower = d[0]
                delay_upper = d[1]
                sched_delay = 1
                call_experiment()
                sched_delay = 0
        elif range_s == "utilization":
            for u in utilization_ranges:
                utilization_lower = u[0]
                utilization_upper = u[1]
                sched_utilization = 1
                call_experiment()
                sched_utilization = 0
                # exit() # temp TODO just want to run the util run
    # return
    for s in ["ias", "simple"]:
        if s == "simple":
            caladan_interval = 5
            caladan_threshold = 5
        else:
            caladan_interval = 10
            caladan_threshold = 10
        scheduler = s
        call_experiment()
        # return
    # spin run
    antagonist = 0
    breakwater_parking = 0
    caladan_interval = 10
    caladan_threshold = 10
    spin_server = 1
    scheduler = "simple"
    call_experiment()
    spin_server = 0
    # num_cores_lc_guaranteed = 0
    antagonist = 1
    # exit()

# if __name__ == "__main__":
#     breakwater_target = 80 # reccomended for 1 us service time and 10 us rtt
#     breakwater_targets = [80]
#     algorithm = "breakwater"
#     connections = 100
#     service_distribution = "exp" 
#     slo = 200
#     breakwater_parking = 1  # set it to 1 to turn on coresync

#     # run through all 5 experiments
#     script_name = "param_synthetic_antagonist.py"
#     service_time = 10

#     # lets just run through static and simple

#     # shennago
#     scheduler = "simple"
#     caladan_interval = 5
#     caladan_threshold = 5
#     call_experiment()
#     caladan_interval = 10
#     caladan_threshold = 10

#     # static
#     # scheduler = "simple"  # for naming purposes
#     # spin_server = 1
#     # num_cores_lc_guaranteed = 16
#     # call_experiment()
#     # spin_server = 0
#     # num_cores_lc_guaranteed = 0


#     # for s in ["ias", "simple", "range_policy", "static"]:
#     #     # SET SCHEDULER
#     #     scheduler = s
#     #     if s == "range_policy":
#     #         caladan_interval = 5
#     #         for range_s in ["delay", "utilization"]:
#     #             if range_s == "delay":
#     #                 for d in delay_ranges:
#     #                     delay_lower = d[0]
#     #                     delay_upper = d[1]
#     #                     sched_delay = 1
#     #                     call_experiment()
#     #                     sched_delay = 0
#     #             elif range_s == "utilization":
#     #                 for u in utilization_ranges:
#     #                     utilization_lower = u[0]
#     #                     utilization_upper = u[1]
#     #                     sched_utilization = 1
#     #                     call_experiment()
#     #                     sched_utilization = 0
#     #         caladan_interval = 10
#     #     elif s == "simple":  # shenango
#     #         caladan_interval = 5
#     #         caladan_threshold = 5
#     #         call_experiment()
#     #         caladan_interval = 10
#     #         caladan_threshold = 10
#     #     elif s == "ias":  # caladan
#     #         caladan_interval = 10
#     #         call_experiment()
#     #     elif s == "static":
#     #         scheduler = "simple"  # for naming purposes
#     #         spin_server = 1
#     #         num_cores_lc_guaranteed = 16
#     #         call_experiment()
#     #         spin_server = 0
#     #         num_cores_lc_guaranteed = 0
#     #     elif s == "coresync":
#     #         scheduler = "ias"
#     #         caladan_interval = 10
#     #         breakwater_parking = 1  # enable coresync
#     #         call_experiment()
#     #         breakwater_parking = 0
def vary_core_credit_ratio():
    global algorithm
    global connections
    global service_time
    global breakwater_target
    global service_distribution
    global offered_load
    global loadshift
    global spin_server
    global num_cores_server
    global num_cores_lc
    global num_cores_lc_guaranteed
    global caladan_threshold
    global slo
    global scheduler
    global delay_ranges
    global utilization_ranges
    global caladan_interval
    global delay_lower
    global delay_upper
    global utilization_lower
    global utilization_upper
    global sched_delay
    global sched_utilization
    global current_load_factor
    global breakwater_parking
    global core_credit_ratio

    global range_loads

    service_time = 10
    breakwater_target = 80
    slo = 200

    scheduler = "ias"
    breakwater_parking = 1
    spin_server = 0
    current_load_factor = 0.7
    # # for lf in [0.4, 0.6]:
    # #     current_load_factor = lf
    for ccr in ccr_values:
        core_credit_ratio = ccr
        # for s in schedulers:
        #     scheduler = s
        #     call_experiment()
        call_experiment()
    # breakwater_parking = 0
    # spin_server = 1
    # scheduler = "simple"
    # num_cores_lc_guaranteed = 16
    # call_experiment()
    # spin_server = 0
    num_cores_lc_guaranteed = 0
    
def vary_parking_and_efficiency_plot():
    global algorithm
    global connections
    global service_time
    global breakwater_target
    global service_distribution
    global offered_load
    global loadshift
    global spin_server
    global num_cores_server
    global num_cores_lc
    global num_cores_lc_guaranteed
    global caladan_threshold
    global slo
    global scheduler
    global delay_ranges
    global utilization_ranges
    global caladan_interval
    global delay_lower
    global delay_upper
    global utilization_lower
    global utilization_upper
    global sched_delay
    global sched_utilization
    global current_load_factor
    global breakwater_parking
    global core_credit_ratio

    global range_loads

    # TODO maybe re run these, and grab EVERY timeseries just for records sake.
    # MAKE SURE to set rebuild to true in the param file for the first run at least.
    # quick range loads for just ias and simple parking
    
    service_time = 10
    breakwater_target = 80
    slo = 200
    core_credit_ratio = 15
    breakwater_parking = 1
    spin_server = 0
    for lf in load_factors:
        current_load_factor = lf
        # for s in schedulers:
        #     scheduler = s
        #     call_experiment()
        scheduler = "ias"
        call_experiment()
    breakwater_parking = 1

    # service_time = 1
    # breakwater_target = 45
    # slo = 110
    # core_credit_ratio = 15
    # breakwater_parking = 1
    # spin_server = 0
    # for lf in load_factors:
    #     current_load_factor = lf
    #     # for s in schedulers:
    #     #     scheduler = s
    #     #     call_experiment()
    #     scheduler = "ias"
    #     call_experiment()
    # breakwater_parking = 0

if __name__ == "__main__":
    vary_core_credit_ratio()
    