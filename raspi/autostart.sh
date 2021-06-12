#!/usr/bin/env bash

# Hide mouse pointer
unclutter -idle 0 &

# Disable screensaver
xset s off
xset s noblank
xset -dpms

# Start server
pushd ~/coffeebuddy
source .env/bin/activate
python bin/run.py &
popd

# Open browser
chromium-browser --incognito --kiosk http://127.0.0.1:5000
