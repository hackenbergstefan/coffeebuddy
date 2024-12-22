#!/usr/bin/env python
import code
import logging
import os
import readline  # optional, will allow Up/Down/History in the console # noqa: F401
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import coffeebuddy  # noqa: E402

try:
    from RPi import GPIO

    GPIO.setmode(GPIO.BCM)
except ModuleNotFoundError:
    pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = coffeebuddy.create_app()
    try:
        with app.app_context():
            coffeebuddy.init_app_context(app)
            from coffeebuddy.model import Drink, Pay, User  # noqa: F401

            variables = globals().copy()
            variables.update(locals())
            shell = code.InteractiveConsole(variables)
            shell.interact()
    except:  # noqa: E722
        raise
