#!/bin/bash

set -e
set -x

git submodule update --init -f --recursive

. build_client.sh

echo building SNAPPY
pushd caladan/apps/storage_service
./snappy.sh
popd

echo building CALADAN
for dir in caladan caladan/shim caladan/bindings/cc caladan/apps/storage_service caladan/apps/netbench; do
	make -C $dir
done


cd ~/protego
pushd caladan/breakwater
sudo ./scripts/setup_machine.sh && make clean && make -j16 && make -C bindings/cc
popd

echo "$SCRIPTPATH"
export SHENANGODIR=$SCRIPTPATH/caladan

# to build SILO properly this SHENAGODIR variable needs to be defined
echo building SILO
pushd  silo
./silo.sh
make
popd


########################
cd memcached && ./version.sh && autoreconf -i && ./configure --with-shenango=../caladan && make clean && make
cd ../memcached-client && make clean && make && cd ..

# TODO
# echo building MEMCACHED
# pushd memcached
# # git checkout breakwater # this shouldn't be necessary once I point it correctly. Also isn't necessary right now when testing with no submodule
# # INHO
# ./version.sh
# autoreconf -i
# # END INHO
# # ./autogen.sh
# ./configure --with-shenango=$SCRIPTPATH/caladan
# make
# popd

# pushd memcached-linux
# ./autogen.sh
# ./configure
# make
# popd

echo building BOEHMGC
pushd gc
./autogen.sh
./configure --prefix=$SCRIPTPATH/gc/build --enable-static --enable-large-config --enable-handle-fork=no --enable-dlopen=no --disable-java-finalization --enable-threads=shenango --enable-shared=no --with-shenango=$SCRIPTPATH/caladan
make install
popd

echo building PARSEC
echo replacing config
cp ./replace/gcc-shenango-gc.bldconf ./parsec/config/ # no real need to modify the parsec repo
for p in x264 swaptions streamcluster; do
	parsec/bin/parsecmgmt -a build -p $p -c gcc-shenango
done
export GCDIR=$SCRIPTPATH/gc/build/
parsec/bin/parsecmgmt -a build -p swaptions -c gcc-shenango-gc
