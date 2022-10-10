#!/bin/bash

cd /rippled
git config --global --add safe.directory $PWD
git rev-parse --short HEAD
cmake -B build -DCMAKE_BUILD_TYPE=Debug -Dunity=Off
cmake --build build --parallel $(nproc)
