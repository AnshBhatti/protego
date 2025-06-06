#!/usr/bin/env python3

import paramiko
import os
from time import sleep
from util import *
from config_remote import *
from datetime import datetime
import random

################################
### Experiemnt Configuration ###
################################

# Server overload algorithm (protego, breakwater, seda, dagor, nocontrol)
OVERLOAD_ALG = "breakwater"

# The number of client connections
NUM_CONNS = 100

# Average service time (in us)
ST_AVG = 10

# make sure these match in bw_config.h
BW_TARGET = 80
BW_THRESHOLD = 160

MAX_KEY_INDEX = 100000
POPULATING_LOAD = 200000

print("modifying bw_config.h values for target and threshold")
cmd = "sed -i \'s/#define SBW_DELAY_TARGET.*/#define SBW_DELAY_TARGET\\t\\t\\t{:d}/g\'"\
        " configs/bw_config.h".format(BW_TARGET)
execute_local(cmd)
cmd = "sed -i \'s/#define SBW_DROP_THRESH.*/#define SBW_DROP_THRESH\\t\\t\\t{:d}/g\'"\
        " configs/bw_config.h".format(BW_THRESHOLD)
execute_local(cmd)

cmd = "sed -i \'s/#define SBW_LATENCY_BUDGET.*/#define SBW_LATENCY_BUDGET\\t\\t\\t{:d}/g\'"\
        " configs/bw2_config.h".format(BW_THRESHOLD)
execute_local(cmd)

BREAKWATER_TIMESERIES = True


# Service time distribution
#    exp: exponential
#    const: constant
#    bimod: bimodal
ST_DIST = "exp"

# SLO = 10 * (average RPC processing time + network RTT)
NET_RTT = 10
# slo = (ST_AVG + NET_RTT) * 10
slo = 50
# slo = 999999

# List of offered load
# OFFERED_LOADS = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100,
#                 110, 120, 130, 140, 150, 160]

# OFFERED_LOADS = [100000, 200000, 300000, 400000, 500000, 600000, 700000, 800000, 900000, 1000000, 1100000, 1200000, 1300000, 1400000, 1600000, 2000000, 3000000]
OFFERED_LOADS = [500000, 1000000, 1500000, 2000000, 2500000, 3000000, 3500000, 4000000]
# OFFERED_LOADS = [400000, 500000, 600000, 700000, 800000, 900000, 1000000, 1100000, 1200000, 1300000, 1400000, 1500000, 1600000]
# OFFERED_LOADS = [400000, 600000, 700000, 800000, 900000, 1000000, 1100000, 1200000, 1300000, 1400000]
# OFFERED_LOADS = [3000000, 3500000, 4000000, 4500000, 5000000]
# OFFERED_LOADS = [1200000, 1300000, 1400000, 1500000]
# loadshift = 1 for load shifts in netbench.cc
LOADSHIFT = 0

# schedulers = ["simple", "ias", "range_policy"]
SCHEDULER = "simple"


ENABLE_DIRECTPATH = True
SPIN_SERVER = False
DISABLE_WATCHDOG = False

NUM_CORES_SERVER = 18
NUM_CORES_LC = 16
NUM_CORES_LC_GUARANTEED = 0
NUM_CORES_CLIENT = 16

CALADAN_THRESHOLD = 5
# TODO double check this is working for non range_policy
CALADAN_INTERVAL = 5
BREAKWATER_CORE_PARKING = False
SBW_CORE_PARK_TARGET = 0.6
CORE_CREDIT_RATIO = 15

DELAY_RANGE = False
delay_lower = 0.5
delay_upper = 1
UTILIZATION_RANGE = False
utilization_lower = 0.75
utilization_upper = 0.95

"""
First, we design a queueing-based policy called delay
range which attempts to maintain a specified average queue-
ing delay across all cores within an application. Every core-
allocation interval (every 5 μs), the simulation checks the
average queueing delay. If it is below the specified lower
bound, a core is revoked; if it is above the upper bound, a core
is added. Similarly, with our utilization range policy, a core
is added or removed whenever the average CPU utilization
over the past interval (fraction of time spent handling tasks)
falls outside the specified range.
"""

AVOID_LARGE_DOWNLOADS = False


DOWNLOAD_ALL_TASKS = True
if DOWNLOAD_ALL_TASKS:
    cmd = "sed -i \'s/#define ENABLE_DOWNLOAD_ALL_TASKS.*/#define ENABLE_DOWNLOAD_ALL_TASKS\\t\\t\\t true/g\'"\
        " replace/netbench.cc"
    execute_local(cmd)
else:
    cmd = "sed -i \'s/#define ENABLE_DOWNLOAD_ALL_TASKS.*/#define ENABLE_DOWNLOAD_ALL_TASKS\\t\\t\\t false/g\'"\
        " replace/netbench.cc"
    execute_local(cmd)

ENABLE_ANTAGONIST = False

IAS_DEBUG = False

ERIC_CSV_NAMING = True
CSV_NAME_DIR = True

# number of threads for antagonist
threads = 4
# units of work each thread attempts at once
work_units = 10
# config string describing what type of antagonist worker, and other variables
# ex. random mem, cache, strided mem, etc. Also control size of buffer and other per worker variables.
# Doing this for max val of an unsigned 32 bit int
random_seed = random.randint(0, 4294967295)
# this was the size of the cache antagonist example from the repo. Seems to be close to a possible L1 size (a big L1 at least)
antagonist_mem_size = 4090880
# cacheantagonist:4090880
# randmem:69:seed
antagonist_param = "randmem:{:d}:{:d}".format(antagonist_mem_size, random_seed)

############################
### End of configuration ###
############################


# Verify configs #
if OVERLOAD_ALG not in ["protego", "breakwater", "seda", "dagor", "nocontrol"]:
    print("Unknown overload algorithm: " + OVERLOAD_ALG)
    exit()

if ST_DIST not in ["exp", "const", "bimod"]:
    print("Unknown service time distribution: " + ST_DIST)
    exit()

### Function definitions ###
def generate_shenango_config(is_server ,conn, ip, netmask, gateway, num_cores,
        directpath, spin, disable_watchdog, latency_critical=False, guaranteed_kthread=0, antagonist="none"):
    config_name = ""
    config_string = ""
    if is_server:
        config_name = "server.config"
        config_string = "host_addr {}".format(ip)\
                      + "\nhost_netmask {}".format(netmask)\
                      + "\nhost_gateway {}".format(gateway)\
                      + "\nruntime_kthreads {:d}".format(num_cores)
        if latency_critical:
            config_string += "\nruntime_priority lc"
            # config_string += "\nruntime_ht_punish_us 10000" # paper says "infinite" for memcached. Defaulting to 0 so
        else:
            config_string += "\nruntime_priority be"
        config_string += "\nruntime_guaranteed_kthreads {:d}".format(guaranteed_kthread)
        config_string += "\nruntime_qdelay_us {:d}".format(CALADAN_THRESHOLD)
        if DELAY_RANGE:
            config_string += "\nruntime_qdelay_lower_thresh_ns {:d}".format(int(delay_lower*1000))
            config_string += "\nruntime_qdelay_upper_thresh_ns {:d}".format(int(delay_upper*1000))
        if UTILIZATION_RANGE:
            config_string += "\nruntime_util_lower_thresh {:f}".format(utilization_lower)
            config_string += "\nruntime_util_upper_thresh {:f}".format(utilization_upper)
        if BREAKWATER_CORE_PARKING and antagonist == "none" and OVERLOAD_ALG == "breakwater":
            print("breakwater prevent parking going into server config")
            config_string += "\nbreakwater_prevent_parks {:f}".format(SBW_CORE_PARK_TARGET) # I don't think we want this behavior to be on anything but netbench w/breakwater
            config_string += "\nbreakwater_core_credit_ratio {:d}".format(CORE_CREDIT_RATIO)
    else:
        config_name = "client.config"
        config_string = "host_addr {}".format(ip)\
                      + "\nhost_netmask {}".format(netmask)\
                      + "\nhost_gateway {}".format(gateway)\
                      + "\nruntime_kthreads {:d}".format(num_cores)
    
    if antagonist != "none":
        config_name = antagonist
        # config_string += "\nenable_gc 1"

    if spin:
        config_string += "\nruntime_spinning_kthreads {:d}".format(num_cores)
    else:
        config_string += "\nruntime_spinning_kthreads 0"

    if directpath:
        config_string += "\nenable_directpath 1"

    if disable_watchdog:
        config_string += "\ndisable_watchdog 1"

    cmd = "cd ~/{} && echo \"{}\" > {} "\
            .format(ARTIFACT_PATH,config_string, config_name)

    return execute_remote([conn], cmd, True)
### End of function definition ###

NUM_AGENT = len(AGENTS)
print ("number of agents: {:d}".format(NUM_AGENT))

# configure Shenango IPs for config
# TODO does each app on shenango need a unique server ip?
antagonist_ip = "192.168.1.7"
server_ip = "192.168.1.200"
client_ip = "192.168.1.100"
agent_ips = []
netmask = "255.255.255.0"
gateway = "192.168.1.1"

for i in range(NUM_AGENT):
    agent_ip = "192.168.1." + str(101 + i)
    agent_ips.append(agent_ip)

k = paramiko.RSAKey.from_private_key_file(KEY_LOCATION)
# connection to server
server_conn = paramiko.SSHClient()
server_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
server_conn.connect(hostname = SERVERS[0], username = USERNAME, pkey = k)

# connection to client
client_conn = paramiko.SSHClient()
client_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client_conn.connect(hostname = CLIENT, username = USERNAME, pkey = k)

# connections to agents
agent_conns = []
for agent in AGENTS:
    agent_conn = paramiko.SSHClient()
    agent_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    agent_conn.connect(hostname = agent, username = USERNAME, pkey = k)
    agent_conns.append(agent_conn)

# Clean-up environment
print("Cleaning up machines...")
cmd = "sudo killall -9 memcached"
execute_remote([server_conn], cmd, True, False)

cmd = "sudo killall -9 mcclient"
execute_remote([client_conn] + agent_conns,
               cmd, True, False)
cmd = "sudo killall -9 iokerneld && sudo killall -9 stress_shm_query"\
      " && sudo killall -9 stress"
execute_remote([server_conn, client_conn] + agent_conns,
               cmd, True, False)
sleep(1)

# Remove temporary output
cmd = "cd ~/{} && rm output.csv output.json".format(ARTIFACT_PATH)
execute_remote([client_conn], cmd, True, False)

# Distribuing config files
print("Distributing configs...")
# - server
cmd = "scp -P 22 -i {} -o StrictHostKeyChecking=no configs/*.h"\
        " {}@{}:~/{}/{}/breakwater/src/ >/dev/null"\
        .format(KEY_LOCATION, USERNAME, SERVERS[0], ARTIFACT_PATH, KERNEL_NAME)
execute_local(cmd)
# - client
cmd = "scp -P 22 -i {} -o StrictHostKeyChecking=no configs/*.h"\
        " {}@{}:~/{}/{}/breakwater/src/ >/dev/null"\
        .format(KEY_LOCATION, USERNAME, CLIENT, ARTIFACT_PATH, KERNEL_NAME)
execute_local(cmd)
# - agents
for agent in AGENTS:
    cmd = "scp -P 22 -i {} -o StrictHostKeyChecking=no configs/*.h"\
            " {}@{}:~/{}/{}/breakwater/src/ >/dev/null"\
            .format(KEY_LOCATION, USERNAME, agent, ARTIFACT_PATH, KERNEL_NAME)
    execute_local(cmd)

# adding to server
if IAS_DEBUG:
    print("Replacing ias.h")
    # - server
    cmd = "scp -P 22 -i {} -o StrictHostKeyChecking=no replace/ias.h"\
            " {}@{}:~/{}/{}/iokernel/"\
            .format(KEY_LOCATION, USERNAME, SERVERS[0], ARTIFACT_PATH, KERNEL_NAME)
    execute_local(cmd)

if True:
    print("replacing bw_server.c")
    cmd = "scp -P 22 -i {} -o StrictHostKeyChecking=no replace/bw_server.c"\
            " {}@{}:~/{}/{}/breakwater/src/"\
            .format(KEY_LOCATION, USERNAME, SERVERS[0], ARTIFACT_PATH, KERNEL_NAME)
    execute_local(cmd)

# Generating config files
print("Generating config files...")
generate_shenango_config(True, server_conn, server_ip, netmask, gateway,
                         NUM_CORES_LC, ENABLE_DIRECTPATH, SPIN_SERVER, DISABLE_WATCHDOG,
                         latency_critical=True, guaranteed_kthread=NUM_CORES_LC_GUARANTEED)
generate_shenango_config(True, server_conn, antagonist_ip, netmask, gateway,
                         NUM_CORES_SERVER, ENABLE_DIRECTPATH, False, DISABLE_WATCHDOG,
                         latency_critical=False, guaranteed_kthread=0, antagonist="antagonist.config")
generate_shenango_config(False, client_conn, client_ip, netmask, gateway,
                         NUM_CORES_CLIENT, ENABLE_DIRECTPATH, True, False)
for i in range(NUM_AGENT):
    generate_shenango_config(False, agent_conns[i], agent_ips[i], netmask,
                             gateway, NUM_CORES_CLIENT, ENABLE_DIRECTPATH, True, False)


if ENABLE_ANTAGONIST:
    # - server
    cmd = "scp -P 22 -i {} -o StrictHostKeyChecking=no replace/stress.cc"\
            " {}@{}:~/{}/{}/apps/netbench/"\
            .format(KEY_LOCATION, USERNAME, SERVERS[0], ARTIFACT_PATH, KERNEL_NAME)
    execute_local(cmd)

if BREAKWATER_TIMESERIES:
    cmd = "cd ~/{}/{}/breakwater && sed -i \'s/#define SBW_TS_OUT.*/#define SBW_TS_OUT\\t\\t\\t true/\'"\
        " src/bw_server.c".format(ARTIFACT_PATH, KERNEL_NAME)
    execute_remote([server_conn], cmd)
else:
    cmd = "cd ~/{}/{}/breakwater && sed -i \'s/#define SBW_TS_OUT.*/#define SBW_TS_OUT\\t\\t\\t false/\'"\
        " src/bw_server.c".format(ARTIFACT_PATH, KERNEL_NAME)
    execute_remote([server_conn], cmd)

# Rebuild Shanango
print("Building Shenango/Caladan...")
cmd = "cd ~/{}/{} && make clean && make && make -C bindings/cc"\
        .format(ARTIFACT_PATH, KERNEL_NAME)
execute_remote([server_conn, client_conn] + agent_conns, cmd, True)

# Build Breakwater
print("Building Breakwater...")
cmd = "cd ~/{}/{}/breakwater && make clean && make && make -C bindings/cc"\
        .format(ARTIFACT_PATH, KERNEL_NAME)
execute_remote([server_conn, client_conn] + agent_conns, cmd, True)

# Build Memcached
print("Building memcached...")
cmd = "cd ~/{}/memcached && make clean && make"\
        .format(ARTIFACT_PATH)
execute_remote([server_conn], cmd, True)

# Build McClient
print("Building mcclient...")
cmd = "cd ~/{}/memcached-client && make clean && make"\
        .format(ARTIFACT_PATH)
execute_remote([client_conn] + agent_conns, cmd, True)

# Execute IOKernel
iok_sessions = []
print("starting server IOKernel")
if DELAY_RANGE or UTILIZATION_RANGE:
    cmd = "cd ~/{}/{} && sudo ./iokerneld simple range_policy interval {:d} 2>&1 | ts %s > iokernel.node-0.log".format(ARTIFACT_PATH, KERNEL_NAME, CALADAN_INTERVAL)
else:
    cmd = "cd ~/{}/{} && sudo ./iokerneld {} interval {:d} 2>&1 | ts %s > iokernel.node-0.log".format(ARTIFACT_PATH, KERNEL_NAME, SCHEDULER, CALADAN_INTERVAL)
iok_sessions += execute_remote([server_conn], cmd, False)

print("starting client/agent IOKernel")
cmd = "cd ~/{}/{} && sudo ./iokerneld simple 2>&1 | ts %s > iokernel.node-1.log".format(ARTIFACT_PATH, KERNEL_NAME)
iok_sessions += execute_remote([client_conn], cmd, False)

count = 2
for agent_node in agent_conns:
    cmd = "cd ~/{}/{} && sudo ./iokerneld simple 2>&1 | ts %s > iokernel.node-{:d}.log".format(ARTIFACT_PATH, KERNEL_NAME, count)
    iok_sessions += execute_remote([agent_node], cmd, False)
    count += 1
sleep(1)


for offered_load in OFFERED_LOADS:

    if ENABLE_ANTAGONIST:
        print("Starting server antagonist")
        cmd = "cd ~/{} && sudo ./{}/apps/netbench/stress antagonist.config {:d} {:d}"\
                " {} > antagonist.csv 2>&1".format(ARTIFACT_PATH, KERNEL_NAME, threads, work_units, antagonist_param)
        server_stress_session = execute_remote([server_conn], cmd, False)
        sleep(1)

    print("Load = {:d}".format(offered_load))
    # Start memcached
    print("Starting Memcached server...")
    cmd = "cd ~/{} && sudo ./memcached/memcached {} server.config"\
            " -p 8001 -v -c 32768 -m 64000 -b 32768 -o hashpower=18"\
            .format(ARTIFACT_PATH, OVERLOAD_ALG)
    server_session = execute_remote([server_conn], cmd, False)
    server_session = server_session[0]

    sleep(2)
    print("Populating entries...")
    cmd = "cd ~/{} && sudo ./memcached-client/mcclient {} client.config client {:d} {} SET"\
            " {:d} {:d} {:d} {:d} 1 >stdout.out 2>&1"\
            .format(ARTIFACT_PATH, OVERLOAD_ALG, NUM_CONNS, server_ip, MAX_KEY_INDEX,
                    slo, 0, POPULATING_LOAD)
    client_session = execute_remote([client_conn], cmd, False)
    client_session = client_session[0]

    client_session.recv_exit_status()

    sleep(1)

    # Remove temporary output
    cmd = "cd ~/{} && rm output.csv output.json".format(ARTIFACT_PATH)
    execute_remote([client_conn], cmd, True, False)

    # getting PIDs
    # server netbench stress_shm_query swaptions iokerneld
    print("grab PIDs at server")
    cmd = "cd ~ && echo memcached > PID.txt && pidof memcached >> PID.txt"
    execute_remote([server_conn], cmd, True)
    if ENABLE_ANTAGONIST:
        cmd = "cd ~ && echo antagonist >> PID.txt && pidof stress >> PID.txt"
        execute_remote([server_conn], cmd, True)
    cmd = "cd ~ && echo iokerneld >> PID.txt && pidof iokerneld >> PID.txt"
    execute_remote([server_conn], cmd, True)
    # cmd = "cd ~ && echo stress_shm_query >> PID.txt && pidof stress_shm_query >> PID.txt"
    # execute_remote([server_conn], cmd, True)
    sleep(1)

    # - clients
    print("\tExecuting client...")
    client_agent_sessions = []
    cmd = "cd ~/{} && sudo ./memcached-client/mcclient {} client.config client {:d} {}"\
            " USR {:d} {:d} {:d} {:d} 0 >stdout.out 2>&1"\
            .format(ARTIFACT_PATH, OVERLOAD_ALG, NUM_CONNS, server_ip,
                    MAX_KEY_INDEX, slo, NUM_AGENT, offered_load)
    client_agent_sessions += execute_remote([client_conn], cmd, False)

    sleep(1)

    # - Agents
    print("\tExecuting agents...")
    cmd = "cd ~/{} && sudo ./memcached-client/mcclient {} client.config agent {}"\
            " >stdout.out 2>&1".format(ARTIFACT_PATH, OVERLOAD_ALG, client_ip)
    client_agent_sessions += execute_remote(agent_conns, cmd, False)

    # Wait for client and agents
    print("\tWaiting for client and agents...")
    for client_agent_session in client_agent_sessions:
        client_agent_session.recv_exit_status()

    sleep(2)
    # Kill server
    cmd = "sudo killall -9 memcached"
    execute_remote([server_conn], cmd, True)

    # Wait for the server
    server_session.recv_exit_status()

    # kill shm query
    # print("killing stress shm queries")
    # cmd = "sudo killall -9 stress_shm_query"
    # execute_remote([server_conn], cmd, True)
    # server_shmqueryBW_session[0].recv_exit_status()
    # server_shmquerySWAPTIONS_session[0].recv_exit_status()
    if ENABLE_ANTAGONIST:
        # kill antagonist
        print("killing server antagonist")
        cmd = "sudo killall -9 stress"
        execute_remote([server_conn], cmd, True, False) # TODO
        server_stress_session[0].recv_exit_status()

    sleep(1)

# Kill IOKernel
cmd = "sudo killall -9 iokerneld"
execute_remote([server_conn, client_conn] + agent_conns, cmd, True)

# Wait for IOKernel sessions
for iok_session in iok_sessions:
    iok_session.recv_exit_status()

# Close connections
server_conn.close()
client_conn.close()
for agent_conn in agent_conns:
    agent_conn.close()

# Create output directory
if not os.path.exists("outputs"):
    os.mkdir("outputs")

# Move output.csv and output.json
print("Collecting outputs...")
cmd = "scp -P 22 -i {} -o StrictHostKeyChecking=no {}@{}:~/{}/output.csv ./"\
        " >/dev/null".format(KEY_LOCATION, USERNAME, CLIENT, ARTIFACT_PATH)
execute_local(cmd)

output_prefix = "memcached_{}".format(OVERLOAD_ALG)
eric_prefix = "memcached_{}".format(OVERLOAD_ALG)

if OVERLOAD_ALG == "breakwater":
    eric_prefix += "_{:d}_{:d}".format(BW_TARGET, BW_THRESHOLD)
    output_prefix += "_{:d}_{:d}".format(BW_TARGET, BW_THRESHOLD)

if NUM_CORES_LC_GUARANTEED > 0:
    eric_prefix += "_guaranteed"

if SPIN_SERVER:
    output_prefix += "_spin"
    eric_prefix += "_spinning"

if DISABLE_WATCHDOG:
    output_prefix += "_nowd"

if ENABLE_ANTAGONIST:
    output_prefix += "_antagonist"
    eric_prefix += "_antagonist"
output_prefix += "_{:d}cores".format(NUM_CORES_SERVER)
output_prefix += "_{:d}load".format(OFFERED_LOADS[0])
# Assuming 16 cores consistently for now, so not adding cores to prefix
if LOADSHIFT:
    eric_prefix += "_loadshift"
else:
    eric_prefix += "_{:d}k".format(int(OFFERED_LOADS[0] / 1000))

eric_prefix += "_{:d}cores".format(NUM_CORES_LC)
eric_prefix += "_{:d}conns".format(NUM_CONNS)
eric_prefix += "_{:d}nodes".format(len(NODES))
if UTILIZATION_RANGE:
    eric_prefix += "_utilization_range_{}_{}".format(utilization_lower, utilization_upper)
elif DELAY_RANGE:
    eric_prefix += "_delay_range_{}_{}".format(delay_lower, delay_upper)
else:
    eric_prefix += "_{}".format(SCHEDULER)

if BREAKWATER_CORE_PARKING:
    eric_prefix += "_park_{}".format(SBW_CORE_PARK_TARGET)

output_prefix += "_{}_{:d}_nconn_{:d}".format(ST_DIST, ST_AVG, NUM_CONNS)

# Print Headers
header = "num_clients,offered_load,throughput,goodput,cpu,min,mean,p50,p90,p99,p999,p9999"\
        ",max,lmin,lmean,lp50,lp90,lp99,lp999,lp9999,lmax,p1_win,mean_win,p99_win,p1_q,mean_q,p99_q,server:rx_pps"\
        ",server:tx_pps,server:rx_bps,server:tx_bps,server:rx_drops_pps,server:rx_ooo_pps"\
        ",server:winu_rx_pps,server:winu_tx_pps,server:win_tx_wps,server:req_rx_pps"\
        ",server:resp_tx_pps,client:min_tput,client:max_tput"\
        ",client:winu_rx_pps,client:winu_tx_pps,client:resp_rx_pps,client:req_tx_pps"\
        ",client:win_expired_wps,client:req_dropped_rps"

curr_date = datetime.now().strftime("%m_%d_%Y")
curr_time = datetime.now().strftime("%H-%M-%S")
output_dir = "outputs/{}".format(curr_date)
if not os.path.isdir(output_dir):
   os.makedirs(output_dir)

run_dir = output_dir + "/" + curr_time
if not os.path.isdir(run_dir):
   os.makedirs(run_dir)

cmd = "echo \"{}\" > {}/{}.csv".format(header, run_dir, curr_time + "-" + output_prefix)
execute_local(cmd)

cmd = "cat output.csv >> {}/{}.csv".format(run_dir, curr_time + "-" + output_prefix)
execute_local(cmd)

if ERIC_CSV_NAMING:
    cmd = "mv {}/{}.csv {}/{}.csv".format(run_dir, curr_time + "-" + output_prefix, run_dir, eric_prefix)
    execute_local(cmd)

if DOWNLOAD_ALL_TASKS and not AVOID_LARGE_DOWNLOADS:
    print("Fetching raw output (all non rejected tasks)")
    cmd = "rsync -azh --info=progress2 -e \"ssh -i {} -o StrictHostKeyChecking=no -o"\
          " UserKnownHostsFile=/dev/null\" {}@{}:~/{}/all_tasks.csv {}/".format(KEY_LOCATION, 
                                                                                        USERNAME, CLIENT, ARTIFACT_PATH, run_dir)
    execute_local(cmd)

if ENABLE_ANTAGONIST:
    print("Fetching antagonist output")
    cmd = "rsync -azh --info=progress2 -e \"ssh -i {} -o StrictHostKeyChecking=no -o"\
          " UserKnownHostsFile=/dev/null\" {}@{}:~/{}/antagonist.csv {}/".format(KEY_LOCATION, 
                                                                                        USERNAME, SERVERS[0], ARTIFACT_PATH, run_dir)
    execute_local(cmd)

# Remove temp outputs
cmd = "rm output.csv"
execute_local(cmd, False)


# TODO put these all in one folder on server so I can just fetch with one command
if not IAS_DEBUG or not AVOID_LARGE_DOWNLOADS:
    print("iokernel log node 0")
    cmd = "rsync -azh --info=progress2 -e \"ssh -i {} -o StrictHostKeyChecking=no -o"\
        " UserKnownHostsFile=/dev/null\" {}@{}:~/{}/caladan/iokernel.node-0.log {}/".format(KEY_LOCATION, USERNAME, SERVERS[0], ARTIFACT_PATH, run_dir)
    execute_local(cmd)

print("stdout node 0")
cmd = "rsync -azh --info=progress2 -e \"ssh -i {} -o StrictHostKeyChecking=no -o"\
        " UserKnownHostsFile=/dev/null\" {}@{}:~/{}/stdout.out {}/ >/dev/null".format(KEY_LOCATION, USERNAME, SERVERS[0], ARTIFACT_PATH, run_dir)
execute_local(cmd)

print("PID.txt node 0")
cmd = "rsync -azh --info=progress2 -e \"ssh -i {} -o StrictHostKeyChecking=no -o"\
        " UserKnownHostsFile=/dev/null\" {}@{}:~/PID.txt {}/ >/dev/null".format(KEY_LOCATION, USERNAME, SERVERS[0], run_dir)
execute_local(cmd)

cmd = "mv {}/stdout.out {}/stdout_server.out".format(run_dir, run_dir)
execute_local(cmd)

print("iokernel log node 1")
cmd = "rsync -azh --info=progress2 -e \"ssh -i {} -o StrictHostKeyChecking=no -o"\
        " UserKnownHostsFile=/dev/null\" {}@{}:~/{}/caladan/iokernel.node-1.log {}/ >/dev/null".format(KEY_LOCATION, USERNAME, CLIENT, ARTIFACT_PATH, run_dir)
execute_local(cmd)

print("stdout client node 1")
cmd = "rsync -azh --info=progress2 -e \"ssh -i {} -o StrictHostKeyChecking=no -o"\
        " UserKnownHostsFile=/dev/null\" {}@{}:~/{}/stdout.out {}/ >/dev/null".format(KEY_LOCATION, USERNAME, CLIENT, ARTIFACT_PATH, run_dir)
execute_local(cmd)
if DOWNLOAD_ALL_TASKS and not AVOID_LARGE_DOWNLOADS:
    print("server drop tasks")
    cmd = "rsync -azh --info=progress2 -e \"ssh -i {} -o StrictHostKeyChecking=no -o"\
        " UserKnownHostsFile=/dev/null\" {}@{}:~/{}/server_drop_tasks.csv {}/ >/dev/null".format(KEY_LOCATION, USERNAME, CLIENT, ARTIFACT_PATH, run_dir)
    execute_local(cmd)

    print("client dropped tasks")
    cmd = "rsync -azh --info=progress2 -e \"ssh -i {} -o StrictHostKeyChecking=no -o"\
        " UserKnownHostsFile=/dev/null\" {}@{}:~/{}/client_drop_tasks.csv {}/ >/dev/null".format(KEY_LOCATION, USERNAME, CLIENT, ARTIFACT_PATH, run_dir)
    execute_local(cmd)
if BREAKWATER_TIMESERIES:
    print("grabbing bw_server timeseries")
    cmd = "scp -P 22 -i {} -o StrictHostKeyChecking=no {}@{}:~/{}/timeseries.csv {}/"\
        " >/dev/null".format(KEY_LOCATION, USERNAME, SERVERS[0], ARTIFACT_PATH, run_dir)
    execute_local(cmd)
    with open("{}/timeseries.csv".format(run_dir)) as original:
        data = original.read()
    execute_local("rm {}/timeseries.csv".format(run_dir))
    with open("{}/timeseries.csv".format(run_dir), "w+") as modified:
        modified.write("timestamp,credit_pool,credit_used,num_pending,num_drained,num_active,num_sess,delay,num_cores,avg_st,successes\n" + data)

print("gathering config options for this experiment")
config_dir = run_dir + "/config"
if not os.path.isdir(config_dir):
   os.makedirs(config_dir)

cmd = "scp -P 22 -i {} -o StrictHostKeyChecking=no {}@{}:~/{}/server.config {}/"\
        " >/dev/null".format(KEY_LOCATION, USERNAME, SERVERS[0], ARTIFACT_PATH, config_dir)
execute_local(cmd)
cmd = "scp -P 22 -i {} -o StrictHostKeyChecking=no {}@{}:~/{}/client.config {}/"\
        " >/dev/null".format(KEY_LOCATION, USERNAME, CLIENT, ARTIFACT_PATH, config_dir)
execute_local(cmd)
if ENABLE_ANTAGONIST:
    cmd = "scp -P 22 -i {} -o StrictHostKeyChecking=no {}@{}:~/{}/antagonist.config {}/"\
        " >/dev/null".format(KEY_LOCATION, USERNAME, SERVERS[0], ARTIFACT_PATH, config_dir)
    execute_local(cmd)
cmd = "cp configs/bw_config.h {}/ && cp configs/bw2_config.h {}/".format(config_dir, config_dir)
execute_local(cmd)
script_config = "overload algorithm: {}\n".format(OVERLOAD_ALG)
script_config += "number of nodes: {}\n".format(len(NODES))
script_config += "number of connections: {}\n".format(NUM_CONNS)
script_config += "service time distribution: {}\n".format(ST_DIST)
script_config += "average service time: {}\n".format(ST_AVG)
script_config += "offered load: {}\n".format(OFFERED_LOADS[0])
script_config += "server cores: {}\n".format(NUM_CORES_SERVER)
script_config += "LC cores: {}\n".format(NUM_CORES_LC)
script_config += "LC guaranteed cores: {}\n".format(NUM_CORES_LC_GUARANTEED)
if SPIN_SERVER:
    script_config += "server cores spinning for LC\n"
script_config += "client cores: {}\n".format(NUM_CORES_CLIENT)
script_config += "caladan threshold: {}\n".format(CALADAN_THRESHOLD)
if ENABLE_ANTAGONIST:
    script_config += "antagonist threads: {}, work_unit {}, command line arg: {}\n".format(threads, work_units, antagonist_param)
script_config += "RTT: {}\n".format(NET_RTT)
script_config += "SLO: {}\n".format(slo)
script_config += "Connections: {:d}\n".format(NUM_CONNS)
script_config += "loadshift: {}\n".format(LOADSHIFT)
script_config += "scheduler: {}\n".format(SCHEDULER)
script_config += "allocation interval: {}\n".format(CALADAN_INTERVAL)
script_config += "breakwater parking scheme: {}\n".format(BREAKWATER_CORE_PARKING)
script_config += "breakwater parking scale factor: {}\n".format(SBW_CORE_PARK_TARGET)

cmd = "echo \"{}\" > {}/script.config".format(script_config, config_dir)
execute_local(cmd)

# produce the cores if applicable
if IAS_DEBUG and not AVOID_LARGE_DOWNLOADS:
    print("creating cores csv")
    cmd = "cd {} && python3 ../../../graph_scripts/create_corecsv.py".format(run_dir)
    execute_local(cmd)

if CSV_NAME_DIR:
    os.chdir(output_dir)
    if os.path.isdir(eric_prefix):
        print("error, desired directory name is already an output directory")
        exit()
    os.rename(curr_time, eric_prefix)
    os.chdir("..")

print("Done.")
# TODO make sure the output stuff is consistent across run scripts
