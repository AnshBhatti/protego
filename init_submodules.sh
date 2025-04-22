#!/bin/sh

set -e

# Initialize submodules
# git submodule init
# git submodule update --init
############# we no longer do this because the submodules are inited in build_all.sh

# Cloudlab patches to Shenango
############# these patches fail for that reason
echo Applying patch to Shenango
cd caladan
git apply ../connectx-4.patch
git apply ../cloudlab_xl170.patch
cd ..

echo Done.
