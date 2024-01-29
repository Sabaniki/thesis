#!/bin/zsh
for i in {1..1000} ; do
    python3 ./latency.py
done
echo "\a"