#!/usr/bin/env python3

import paramiko
import os
from time import sleep
from util import *
from config_remote import *
from datetime import datetime

################################
### Experiemnt Configuration ###
################################

# Server overload algorithm (protego, breakwater, seda, dagor, nocontrol)
OVERLOAD_ALG = "breakwater"

# The number of client connections
NUM_CONNS = 1000

# Average service time (in us)
ST_AVG = 1

# Service time distribution
#    exp: exponential
#    const: constant
#    bimod: bimodal
ST_DIST = "exp"

# List of offered load
# OFFERED_LOADS = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100,
#                 110, 120, 130, 140, 150, 160]

# OFFERED_LOADS = [400000, 800000, 1200000]
OFFERED_LOADS = [800000]

# for i in range(len(OFFERED_LOADS)):
#     OFFERED_LOADS[i] *= 10000

ENABLE_DIRECTPATH = True
SPIN_SERVER = False
DISABLE_WATCHDOG = False

NUM_CORES_SERVER = 17
NUM_CORES_CLIENT = 16

CALADAN_THRESHOLD = 10

DOWNLOAD_RAW = False

############################
### End of configuration ###
############################

# SLO = 10 * (average RPC processing time + network RTT)
NET_RTT = 10
slo = (ST_AVG + NET_RTT) * 10
# slo = 200

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
        else:
            config_string += "\nruntime_priority be"
        config_string += "\nruntime_guaranteed_kthreads {:d}".format(guaranteed_kthread)
        config_string += "\nruntime_qdelay_us {:d}".format(CALADAN_THRESHOLD)
    else:
        config_name = "client.config"
        config_string = "host_addr {}".format(ip)\
                      + "\nhost_netmask {}".format(netmask)\
                      + "\nhost_gateway {}".format(gateway)\
                      + "\nruntime_kthreads {:d}".format(num_cores)
    
    if antagonist != "none":
        config_name = antagonist
        config_string += "\nenable_gc 1"

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

# configure Shenango IPs for config
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
cmd = "sudo killall -9 netbench & sudo killall -9 iokerneld && sudo killall -9 stress_shm_query"\
      " && sudo killall -9 swaptions"
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

# Generating config files
print("Generating config files...")
generate_shenango_config(True, server_conn, server_ip, netmask, gateway,
                         NUM_CORES_SERVER, ENABLE_DIRECTPATH, SPIN_SERVER, DISABLE_WATCHDOG,
                         latency_critical=True, guaranteed_kthread=16)
generate_shenango_config(True, server_conn, server_ip, netmask, gateway,
                         NUM_CORES_SERVER, ENABLE_DIRECTPATH, SPIN_SERVER, DISABLE_WATCHDOG,
                         latency_critical=False, guaranteed_kthread=0, antagonist="swaptionsGC.config")
generate_shenango_config(False, client_conn, client_ip, netmask, gateway,
                         NUM_CORES_CLIENT, ENABLE_DIRECTPATH, True, False)
for i in range(NUM_AGENT):
    generate_shenango_config(False, agent_conns[i], agent_ips[i], netmask,
                             gateway, NUM_CORES_CLIENT, ENABLE_DIRECTPATH, True, False)

if DOWNLOAD_RAW:
    # - client
    cmd = "scp -P 22 -i {} -o StrictHostKeyChecking=no netbench.cc"\
            " {}@{}:~/{}/{}/breakwater/apps/netbench/"\
            .format(KEY_LOCATION, USERNAME, CLIENT, ARTIFACT_PATH, KERNEL_NAME)
    execute_local(cmd)

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

# Build Netbench
print("Building netbench...")
cmd = "cd ~/{}/{}/breakwater/apps/netbench && make clean && make"\
        .format(ARTIFACT_PATH, KERNEL_NAME)
execute_remote([server_conn, client_conn] + agent_conns, cmd, True)

# Execute IOKernel
iok_sessions = []
print("starting server IOKernel")
cmd = "cd ~/{}/{} && sudo ./iokerneld ias"\
    " 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18  2>&1 | ts %s > iokernel.node-0.log".format(ARTIFACT_PATH, KERNEL_NAME)
iok_sessions += execute_remote([server_conn], cmd, False)

print("starting client/agent IOKernel")
cmd = "cd ~/{}/{} && sudo ./iokerneld simple 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18"\
    " 2>&1 | ts %s > iokernel.node-1.log".format(ARTIFACT_PATH, KERNEL_NAME)
iok_sessions += execute_remote([client_conn], cmd, False)

count = 2
for agent_node in agent_conns:
    cmd = "cd ~/{}/{} && sudo ./iokerneld simple 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18"\
    " 2>&1 | ts %s > iokernel.node-{:d}.log".format(ARTIFACT_PATH, KERNEL_NAME, count)
    iok_sessions += execute_remote([agent_node], cmd, False)
    count += 1
sleep(1)

for offered_load in OFFERED_LOADS:
    # Start swaptions
    print("Starting swaptions application")
    cmd = "cd ~/{} && export SHMKEY=102 &&"\
        " parsec/pkgs/apps/swaptions/inst/amd64-linux.gcc-shenango-gc/bin/swaptions"\
        " swaptionsGC.config -ns 5000000 -sm 400 -nt 17  > swaptionsGC.out 2> swaptionsGC.err".format(ARTIFACT_PATH)
    server_swaptions_session = execute_remote([server_conn], cmd, False)
    sleep(1)

    # Start shm query breakwater mem? what does this mean
    print("Starting shm query breakwater")
    cmd = "cd ~/{} && export SHMKEY=102 &&"\
        " sudo ./caladan/apps/netbench/stress_shm_query membw:1000 > mem.log 2>&1".format(ARTIFACT_PATH)
    server_shmqueryBW_session = execute_remote([server_conn], cmd, False)
    sleep(1)

    # Start shm query from I guess swaptions?
    print("Starting shm query swaptions")
    cmd = "cd ~/{} && export SHMKEY=102 &&"\
        " sudo ./caladan/apps/netbench/stress_shm_query 102:1000:17  > swaptionsGC_shm_query.out 2>&1".format(ARTIFACT_PATH)
    server_shmquerySWAPTIONS_session = execute_remote([server_conn], cmd, False)
    sleep(1)

    print("Load = {:d}".format(offered_load))
    # Execute netbench application
    # - server
    print("\tExecuting server...")
    cmd = "cd ~/{} && sudo ./{}/breakwater/apps/netbench/netbench"\
            " {} server.config server >stdout.out 2>&1"\
            .format(ARTIFACT_PATH, KERNEL_NAME, OVERLOAD_ALG)
    server_session = execute_remote([server_conn], cmd, False)
    server_session = server_session[0]
    
    sleep(1)

    # getting PIDs
    # server netbench stress_shm_query swaptions iokerneld
    print("grab PIDs at server")
    cmd = "cd ~ && echo netbench > PID.txt && pidof netbench >> PID.txt"
    execute_remote([server_conn], cmd, True)
    cmd = "cd ~ && echo swaptions >> PID.txt && pidof swaptions >> PID.txt"
    # execute_remote([server_conn], cmd, True)
    cmd = "cd ~ && echo iokerneld >> PID.txt && pidof iokerneld >> PID.txt"
    execute_remote([server_conn], cmd, True)
    cmd = "cd ~ && echo stress_shm_query >> PID.txt && pidof stress_shm_query >> PID.txt"
    execute_remote([server_conn], cmd, True)
    sleep(1)

    # - client
    print("\tExecuting client...")
    client_agent_sessions = []
    cmd = "cd ~/{} && sudo ./{}/breakwater/apps/netbench/netbench"\
            " {} client.config client {:d} {:f} {} {:d} {:d} {:d} {} {:d}"\
            " >stdout.out 2>&1".format(ARTIFACT_PATH, KERNEL_NAME, OVERLOAD_ALG, NUM_CONNS,
                    ST_AVG, ST_DIST, slo ,NUM_AGENT, offered_load, server_ip, 1)
    client_agent_sessions += execute_remote([client_conn], cmd, False)

    sleep(1)
    
    # - agent
    print("\tExecuting agents...")
    cmd = "cd ~/{} && sudo ./{}/breakwater/apps/netbench/netbench"\
            " {} client.config agent {} >stdout.out 2>&1"\
            .format(ARTIFACT_PATH, KERNEL_NAME, OVERLOAD_ALG, client_ip)
    client_agent_sessions += execute_remote(agent_conns, cmd, False)

    # Wait for client and agents
    print("\tWaiting for client and agents...")
    for client_agent_session in client_agent_sessions:
        client_agent_session.recv_exit_status()

    # Kill server
    cmd = "sudo killall -9 netbench"
    execute_remote([server_conn], cmd, True)

    # Wait for server to be killed
    server_session.recv_exit_status()

    # kill shm query
    print("killing stress shm queries")
    cmd = "sudo killall -9 stress_shm_query"
    execute_remote([server_conn], cmd, True)
    server_shmqueryBW_session[0].recv_exit_status()
    server_shmquerySWAPTIONS_session[0].recv_exit_status()

    # kill swaptions
    print("killing swaptions")
    cmd = "sudo killall -9 swaptions"
    execute_remote([server_conn], cmd, True, False) # TODO
    server_swaptions_session[0].recv_exit_status()

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

output_prefix = "{}".format(OVERLOAD_ALG)

if SPIN_SERVER:
    output_prefix += "_spin"

if DISABLE_WATCHDOG:
    output_prefix += "_nowd"

output_prefix += "_{}_{:d}_nconn_{:d}".format(ST_DIST, ST_AVG, NUM_CONNS)

# Print Headers
header = "num_clients,offered_load,throughput,goodput,cpu"\
        ",min,mean,p50,p90,p99,p999,p9999,max"\
        ",reject_min,reject_mean,reject_p50,reject_p99"\
        ",p1_credit,mean_credit,p99_credit"\
        ",p1_q,mean_q,p99_q,mean_stime,p99_stime,server:rx_pps,server:tx_pps"\
        ",server:rx_bps,server:tx_bps,server:rx_drops_pps,server:rx_ooo_pps"\
        ",server:cupdate_rx_pps,server:ecredit_tx_pps,server:credit_tx_cps"\
        ",server:req_rx_pps,server:req_drop_rate,server:resp_tx_pps"\
        ",client:min_tput,client:max_tput"\
        ",client:ecredit_rx_pps,client:cupdate_tx_pps"\
        ",client:resp_rx_pps,client:req_tx_pps"\
        ",client:credit_expired_cps,client:req_dropped_rps"

curr_date = datetime.now().strftime("%m_%d_%Y")
curr_time = datetime.now().strftime("%H_%M-%S-")
output_dir = "outputs/{}".format(curr_date)
if not os.path.isdir(output_dir):
   os.makedirs(output_dir)

cmd = "echo \"{}\" > {}/{}.csv".format(header, output_dir, curr_time + output_prefix)
execute_local(cmd)

cmd = "cat output.csv >> {}/{}.csv".format(output_dir, curr_time + output_prefix)
execute_local(cmd)

if DOWNLOAD_RAW:
    print("Fetching raw output (all non rejected tasks)")
    cmd = "rsync  -tvz --progress -e \"ssh -i {} -o StrictHostKeyChecking=no -o"\
                " UserKnownHostsFile=/dev/null\" {}@{}:~/{}/all_tasks.csv {}/{}.csv"\
                " >/dev/null".format(KEY_LOCATION, USERNAME, CLIENT, ARTIFACT_PATH, output_dir, curr_time + "all_tasks_" + output_prefix)
    execute_local(cmd)

# Remove temp outputs
cmd = "rm output.csv"
execute_local(cmd, False)

print("Output generated: outputs/{}.csv".format(output_prefix))
print("Done.")
