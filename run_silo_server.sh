#!/bin/bash

LD_LIBRARY_PATH=$(dirname $(find . -name "liblz4.so")) ./silotpcc-shenango
