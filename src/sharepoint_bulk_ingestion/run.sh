#!/usr/bin/bash

cd "$(dirname "$0")"

python3 sharepoint_integration.py -cl info --max-drives -1 --max-items -1 --bulk-item-count 10
