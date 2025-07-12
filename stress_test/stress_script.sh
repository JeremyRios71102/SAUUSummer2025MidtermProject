#!/bin/bash

while true
do
  echo "Running CPU Stress..."
  stress-ng --cpu 2 --timeout 30s

  echo "Running Memory Stress..."
  stress-ng --vm 1 --vm-bytes 512M --timeout 20s

  echo "Running IO stress..."
  stress-ng --io 2 --timeout 25s

  echo "Running HDD stress..."
  stress-ng --hdd 1 --timeout 20s --hdd-bytes 200M

  echo "Running Fork stress..."
  stress-ng --fork 4 --timeout 15s

  echo "Cooling down for 10 seconds..."
  sleep 10
done
