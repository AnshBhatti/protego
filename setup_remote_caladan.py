#!/usr/bin/env python3
import os
import paramiko
from util import *
from config_remote import *

k = paramiko.RSAKey.from_private_key_file(KEY_LOCATION)
# k = paramiko.Ed25519Key.from_private_key_file(KEY_LOCATION)

# config check
if len(NODES) < 1:
    print("[ERROR] There is no server to configure.")
    exit()

# change default shell to bash
print("Changing default shell to bash...")
conns = []
for server in NODES:
    print(server)
    server_conn = paramiko.SSHClient()
    server_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    server_conn.connect(hostname = server, username = USERNAME, pkey = k)
    conns.append(server_conn)

execute_remote(conns, f"sudo usermod -s /bin/bash {USERNAME}", True, False)

for conn in conns:
    conn.close()

# connections to servers
server_conn = paramiko.SSHClient()
server_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
server_conn.connect(hostname = SERVERS[0], username = USERNAME, pkey = k)

conns = []
conns.append(server_conn)
for node in CLIENTS:
    node_conn = paramiko.SSHClient()
    node_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    node_conn.connect(hostname = node, username = USERNAME, pkey = k)
    conns.append(node_conn)

# clean up machines
print("Cleaning up machines...")
cmd = "sudo killall -9 cstate"
execute_remote(conns, cmd, True, False)

cmd = "sudo killall -9 iokerneld"
execute_remote(conns, cmd, True, False)

cmd = f"sudo rm -rf ~/{ARTIFACT_PATH}"
execute_remote(conns, cmd, True, False)

# distributing code-base
print("Distributing sources...")
repo_name = (os.getcwd().split('/'))[-1]
# - server
for server in NODES:
    cmd = f"rsync -azh -e \"ssh -i {KEY_LOCATION} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null\" --info=progress2 --exclude outputs/ ../{repo_name}/ {USERNAME}@{server}:~/{ARTIFACT_PATH}"
    execute_local(cmd)

print("Installing listed Caladan dependencies")
cmd = "sudo apt-get update"
execute_remote(conns, cmd, True)

cmd = "sudo apt-get -y install build-essential libnuma-dev clang autoconf"\
        " autotools-dev m4 automake libevent-dev  libpcre++-dev libtool"\
        " ragel libev-dev moreutils parallel cmake python3 python3-pip"\
        " libjemalloc-dev libaio-dev libdb5.3++-dev numactl hwloc libmnl-dev"\
        " libnl-3-dev libnl-route-3-dev uuid-dev libssl-dev libcunit1-dev pkg-config"
execute_remote(conns, cmd, True)

# excute caladan build scripts
print("Executing caladan build all and build client scripts for main server node. Will make submodules and most components.")
cmd = f"cd ~/{ARTIFACT_PATH} && ./build_all.sh"
execute_remote([server_conn], cmd, True)

print("Executing caladan build client script for other connections")
cmd = f"cd ~/{ARTIFACT_PATH} && ./build_client.sh"
execute_remote(conns[1:], cmd, True)

# settting up machines
# NOTE Inho has his own setup script here, it does also call the caladan setup script
print("Setting up machines...")
cmd = f"cd ~/{ARTIFACT_PATH}/{KERNEL_NAME}/breakwater && sudo ./scripts/setup_machine.sh"
execute_remote(conns, cmd, True)

print("Building Breakwater...")
cmd = f"cd ~/{ARTIFACT_PATH}/{KERNEL_NAME}/breakwater && make clean && make -j16 && make -C bindings/cc"
execute_remote(conns, cmd, True)

# TODO actually might not work in build scripts, since I think breakwater needs to be built first
print("Setting up memcached...")
cmd = f"cd ~/{ARTIFACT_PATH}/memcached && ./version.sh && autoreconf -i && ./configure --with-shenango=../{KERNEL_NAME} && make clean && make"
execute_remote([server_conn], cmd, True)

print("Done.")
