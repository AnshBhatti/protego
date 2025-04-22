

LD_LIBRARY_PATH=$(dirname $(find . -name "liblz4.so")) ./silotpcc-shenango server.config 1 8001 3221225472
./silo-client breakwater client.config client 1 192.168.1.200 0

## why sudo??
sudo ./mcclient breakwater client.config client 1 192.168.1.200 USR 100000 50 0 200000 0
./memcached breakwater server.config  -p 8001 -v -c 32768 -m 64000 -b 32768 -o hashpower=18



clear && ./remake-silo.sh && ./silo-client breakwater client.config client 1 192.168.1.200 USR 100000 50 0 200000 0
pushd ../caladan/breakwater/; make clean && make; popd; make clean && ./remake-silo.sh  && LD_LIBRARY_PATH=$(dirname $(find . -name "liblz4.so")) ./silotpcc-shenango server.config 1 8001 3221225472
