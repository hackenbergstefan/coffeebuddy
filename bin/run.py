#!/usr/bin/env python
import logging
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import coffeebuddy  # noqa: E402

try:
    import RPi.GPIO as GPIO

    GPIO.setmode(GPIO.BCM)
except ModuleNotFoundError:
    pass


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = coffeebuddy.create_app()
    try:
        with app.app_context():
            coffeebuddy.init_app_context()
    except:  # noqa: E722
        raise
    app.socketio.run(app, use_reloader=False)
