#!/bin/bash
set -e

cd ~/dapp/leadservice

echo "LeadService Production Mode"
echo "============================"

# Init data
python3 scripts/init_data.py

# Start Gunicorn
echo "Starting Gunicorn..."
cd backend
exec gunicorn -w 4 -b 0.0.0.0:8001 --access-logfile - --error-logfile - main:app
