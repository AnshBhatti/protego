#!/usr/bin/env python3

import paramiko
import os
from time import sleep
from util import *
from config_remote import *

################################
### Experiemnt Configuration ###
################################
"""

for timeseries, might just have to run this one at a time

"""
# Server overload algorithm (breakwater, seda, dagor, nocontrol)
OVERLOAD_ALG = "breakwater"

# The number of client connections
NUM_CONNS = 100

# List of offered load
OFFERED_LOADS = [500000, 1000000, 1500000, 2000000, 2500000, 3000000, \
                    3500000, 4000000, 4500000, 5000000, 5500000,\
                    6000000, 6500000, 7000000, 7500000, 8000000]

MAX_KEY_INDEX = 100000

ENABLE_DIRECTPATH = True
SPIN_SERVER = False # disabling, I think we default to caladan?
DISABLE_WATCHDOG = False

NUM_CORES_SERVER = 16
NUM_CORES_CLIENT = 16

slo = 50
POPULATING_LOAD = 200000

############################
### End of configuration ###
############################

# Verify configs #
if OVERLOAD_ALG not in ["breakwater", "seda", "dagor", "nocontrol"]:
    print("Unknown overload algorithm: " + OVERLOAD_ALG)
    exit()

cmd = f"sed -i'.orig' -e 's/#define SBW_RTT_US.*/#define SBW_RTT_US\\t\\t\\t{NET_RTT:d}/g' configs/bw_config.h"
execute_local(cmd)

### Function definitions ###
def generate_shenango_config(is_server ,conn, ip, netmask, gateway, num_cores,
        directpath, spin, disable_watchdog):
    config_name = ""
    config_string = ""
    if is_server:
        config_name = "server.config"
        config_string = f"host_addr {ip}"\
                      + f"\nhost_netmask {netmask}"\
                      + f"\nhost_gateway {gateway}"\
                      + f"\nruntime_kthreads {num_cores:d}"
    else:
        config_name = "client.config"
        config_string = f"host_addr {ip}"\
                      + f"\nhost_netmask {netmask}"\
                      + f"\nhost_gateway {gateway}"\
                      + f"\nruntime_kthreads {num_cores:d}"

    if spin:
        config_string += f"\nruntime_spinning_kthreads {num_cores:d}"

    if directpath:
        config_string += "\nenable_directpath 1"

    if disable_watchdog:
        config_string += "\ndisable_watchdog 1"

    cmd = f"cd ~/{ARTIFACT_PATH} && echo \"{config_string}\" > {config_name} "

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
    agent_ip = "192.168.1." + str(101 + i);
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
cmd = "sudo killall -9 memcached & sudo killall -9 iokerneld"
execute_remote([server_conn], cmd, True, False)

cmd = "sudo killall -9 mcclient & sudo killall -9 iokerneld"
execute_remote([client_conn] + agent_conns,
               cmd, True, False)
sleep(1)


# Distribuing config files
print("Distributing configs...")
# - server
cmd = f"scp -P 22 -i {KEY_LOCATION} -o StrictHostKeyChecking=no configs/* {USERNAME}@{SERVERS[0]}:~/{ARTIFACT_PATH}/caladan/breakwater/src/ >/dev/null"
execute_local(cmd)
# - client
cmd = f"scp -P 22 -i {KEY_LOCATION} -o StrictHostKeyChecking=no configs/* {USERNAME}@{CLIENT}:~/{ARTIFACT_PATH}/caladan/breakwater/src/ >/dev/null"
execute_local(cmd)
# - agents
for agent in AGENTS:
    cmd = f"scp -P 22 -i {KEY_LOCATION} -o StrictHostKeyChecking=no configs/* {USERNAME}@{agent}:~/{ARTIFACT_PATH}/caladan/breakwater/src/ >/dev/null"
    execute_local(cmd)

# getting new memcached in there
print("replacing memcached-client")
# - client
cmd = f"scp -P 22 -i {KEY_LOCATION} -o StrictHostKeyChecking=no memcached-client/mcclient.cc {USERNAME}@{CLIENT}:~/{ARTIFACT_PATH}/memcached-client/ >/dev/null"
execute_local(cmd)
# - agents
for agent in AGENTS:
    cmd = f"scp -P 22 -i {KEY_LOCATION} -o StrictHostKeyChecking=no memcached-client/mcclient.cc {USERNAME}@{agent}:~/{ARTIFACT_PATH}/memcached-client/ >/dev/null"
    execute_local(cmd)

# Generating config files
print("Generating config files...")
generate_shenango_config(True, server_conn, server_ip, netmask, gateway,
                         NUM_CORES_SERVER, ENABLE_DIRECTPATH, SPIN_SERVER, DISABLE_WATCHDOG)
generate_shenango_config(False, client_conn, client_ip, netmask, gateway,
                         NUM_CORES_CLIENT, ENABLE_DIRECTPATH, True, False)
for i in range(NUM_AGENT):
    generate_shenango_config(False, agent_conns[i], agent_ips[i], netmask,
                             gateway, NUM_CORES_CLIENT, ENABLE_DIRECTPATH, True, False)

# Rebuild Shanango
print("Building Shenango...")
cmd = f"cd ~/{ARTIFACT_PATH}/caladan && make clean && make && make -C bindings/cc"
execute_remote([server_conn, client_conn] + agent_conns,
               cmd, True)

# Build Breakwater
print("Building Breakwater...")
cmd = f"cd ~/{ARTIFACT_PATH}/caladan/breakwater && make clean && make && make -C bindings/cc"
execute_remote([server_conn, client_conn] + agent_conns,
                 cmd, True)

# Build Memcached
print("Building memcached...")
cmd = f"cd ~/{ARTIFACT_PATH}/memcached && make clean && make"
execute_remote([server_conn], cmd, True)

# Build McClient
print("Building mcclient...")
cmd = f"cd ~/{ARTIFACT_PATH}/memcached-client && make clean && make"
execute_remote([client_conn] + agent_conns, cmd, True)

# Execute IOKernel
iok_sessions = []
print("Executing IOKernel...")
cmd = f"cd ~/{ARTIFACT_PATH}/caladan && sudo ./iokerneld"
iok_sessions += execute_remote([server_conn, client_conn] + agent_conns, cmd, False)

sleep(1)

# Start memcached
print("Starting Memcached server...")
cmd = f"cd ~/{ARTIFACT_PATH} && sudo ./memcached/memcached {OVERLOAD_ALG} server.config -p 8001 -v -c 32768 -m 64000 -b 32768 -o hashpower=18"
server_session = execute_remote([server_conn], cmd, False)
server_session = server_session[0]

sleep(2)
print("Populating entries...")
cmd = f"cd ~/{ARTIFACT_PATH} && sudo ./memcached-client/mcclient {OVERLOAD_ALG} client.config client {NUM_CONNS:d} {server_ip} SET {MAX_KEY_INDEX:d} {slo:d} {0:d} {POPULATING_LOAD:d} >stdout.out 2>&1"
client_session = execute_remote([client_conn], cmd, False)
client_session = client_session[0]

client_session.recv_exit_status()

sleep(1)

# Remove temporary output
cmd = f"cd ~/{ARTIFACT_PATH} && rm output.csv output.json"
execute_remote([client_conn], cmd, True, False)

sleep(1)

for offered_load in OFFERED_LOADS:
    print(f"Load = {offered_load:d}")
    # - clients
    print("\tExecuting client...")
    client_agent_sessions = []
    cmd = f"cd ~/{ARTIFACT_PATH} && sudo ./memcached-client/mcclient {OVERLOAD_ALG} client.config client {NUM_CONNS:d} {server_ip} USR {MAX_KEY_INDEX:d} {slo:d} {NUM_AGENT:d} {offered_load:d} >stdout.out 2>&1"
    client_agent_sessions += execute_remote([client_conn], cmd, False)

    sleep(1)

    # - Agents
    print("\tExecuting agents...")
    cmd = f"cd ~/{ARTIFACT_PATH} && sudo ./memcached-client/mcclient {OVERLOAD_ALG} client.config agent {client_ip} >stdout.out 2>&1"
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
cmd = f"scp -P 22 -i {KEY_LOCATION} -o StrictHostKeyChecking=no {USERNAME}@{CLIENT}:~/{ARTIFACT_PATH}/output.csv ./ >/dev/null"
execute_local(cmd)

output_prefix = f"{OVERLOAD_ALG}"

if SPIN_SERVER:
    output_prefix += "_spin"

if DISABLE_WATCHDOG:
    output_prefix += "_nowd"

output_prefix += f"_memcached_nconn_{NUM_CONNS:d}"

# Print Headers
header = "num_clients,offered_load,throughput,goodput,cpu,min,mean,p50,p90,p99,p999,p9999"\
        ",max,lmin,lmean,lp50,lp90,lp99,lp999,lp9999,lmax,p1_win,mean_win,p99_win,p1_q,mean_q,p99_q,server:rx_pps"\
        ",server:tx_pps,server:rx_bps,server:tx_bps,server:rx_drops_pps,server:rx_ooo_pps"\
        ",server:winu_rx_pps,server:winu_tx_pps,server:win_tx_wps,server:req_rx_pps"\
        ",server:resp_tx_pps,client:min_tput,client:max_tput"\
        ",client:winu_rx_pps,client:winu_tx_pps,client:resp_rx_pps,client:req_tx_pps"\
        ",client:win_expired_wps,client:req_dropped_rps"
cmd = f"echo \"{header}\" > outputs/{output_prefix}.csv"
execute_local(cmd)

cmd = f"cat output.csv >> outputs/{output_prefix}.csv"
execute_local(cmd)

# Remove temp outputs
cmd = "rm output.csv"
execute_local(cmd, False)

print(f"Output generated: outputs/{output_prefix}.csv")
print("Done.")
