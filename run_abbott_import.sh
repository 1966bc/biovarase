#!/bin/bash
# Abbott QC Import wrapper for cron
cd "/home/gcostanzi@intraosa.net/Documents/projects/biovarase"
/usr/bin/python3 abbott_import.py >> abbott_import.log 2>&1
