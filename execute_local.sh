#!/bin/bash

set -e

# sudo do-release-upgrade -f DistUpgradeViewNonInteractive 

sudo apt-get update
sudo apt-get -y install build-essential libnuma-dev clang autoconf \
autotools-dev m4 automake libevent-dev  libpcre++-dev libtool ragel \
libev-dev moreutils parallel cmake python3 python3-pip libjemalloc-dev \
libaio-dev libdb5.3++-dev numactl hwloc libmnl-dev libnl-3-dev libnl-route-3-dev \
uuid-dev libssl-dev libcunit1-dev pkg-config

