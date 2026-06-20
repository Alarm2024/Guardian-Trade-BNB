#!/bin/bash
# 1. Kill any existing bot process
pkill -f guardian_telegram.py

# 2. Export Keys (Put your keys here)
# export TELEGRAM_BOT_TOKEN="YOUR_TOKEN"
# export GEMINI_API_KEY="YOUR_GEMINI_KEY"
# export DEEPSEEK_API_KEY="YOUR_DEEPSEEK_KEY"

# 3. Start the bot in the background
nohup python3 /home/wyndhamdesert/guardian_telegram.py > /home/wyndhamdesert/bot.log 2>&1 &

echo "Pro Guardian Bot is now running in the background."
echo "Check /home/wyndhamdesert/bot.log for errors."
