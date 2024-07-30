#!/usr/bin/env bash

# Hide mouse pointer
unclutter -idle 0 &

# Disable screensaver
xset s off
xset s noblank
xset -dpms

# Start server
screen -S coffeebuddy_server -dm bash -c '
  cd ~/coffeebuddy
  . .venv/bin/activate
  python bin/run.py
'

sleep 20

# Open browser
chromium-browser --kiosk --noerrdialogs --disable-translate --no-first-run --fast --fast-start --disable-infobars --disable-features=TranslateUI http://127.0.0.1:5000
