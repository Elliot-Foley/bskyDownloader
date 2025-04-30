#!/bin/bash

# Kill all producer and consumer Python scripts
echo "Stopping producer and consumer processes..."

pkill -f producer.py
pkill -f consumer.py

echo "All producer and consumer processes have been terminated."

