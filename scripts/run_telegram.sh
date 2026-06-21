#!/bin/bash
export PYTHONPATH=$PYTHONPATH:/home/wyndhamdesert/Guardian-Trade-BNB

echo "[+] Starting Guardian Telegram Bot Listener..."
python3 core/guardian_telegram.py
