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

# Open browser
chromium-browser --kiosk http://127.0.0.1:5000
