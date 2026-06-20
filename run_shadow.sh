#!/bin/bash
echo "[+] Starting Guardian-Trade in SHADOW-TESTING mode..."
# Export dummy credentials or ensure environment is set to non-executing
export SHADOW_MODE=true
export PYTHONPATH=$PYTHONPATH:.
python3 simulate_bot.py
