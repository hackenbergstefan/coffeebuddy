#!/usr/bin/env python
import logging
import os
import sys

import IPython

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
            from coffeebuddy.model import CoffeeVariant, Drink, Pay, User  # noqa: F401

            db = app.db
            dbsession = db.session

            variables = globals().copy()
            variables.update(locals())
            IPython.embed(colors="neutral")
    except:  # noqa: E722
        raise
