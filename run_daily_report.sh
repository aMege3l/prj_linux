#!/usr/bin/env bash
set -euo pipefail

cd /home/projet/prj_linux/prj_linux
source .venv/bin/activate

mkdir -p logs
python scripts/daily_report.py >> logs/cron.log 2>&1
