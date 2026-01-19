#!/bin/bash

# Number of consumer instances to run
N=5

for ((i=1; i<=N; i++)); do
  nohup python3 consumer.py >> "consumer_log_$i.txt" 2>&1 &
  echo "Started consumer instance $i"
done

