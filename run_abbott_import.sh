#!/bin/bash
# Abbott QC Import wrapper for cron
# Runs every 5 minutes, imports only last 7 days of data
cd "/home/gcostanzi@intraosa.net/Documents/projects/biovarase"
/usr/bin/python3 abbott_import_v2.py --days 7 >> abbott_import.log 2>&1
