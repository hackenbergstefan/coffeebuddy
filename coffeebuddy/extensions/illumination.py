#!/usr/bin/env python
import logging

import flask

"""
This extension controls the illumination of the coffeebuddy
using a RGB LED pins on Raspberry Pi.
"""

PIN_GREEN = 16
PIN_BLUE = 20
PIN_RED = 21

pi = None


def setup(pin_red, pin_green, pin_blue):
    global PIN_RED, PIN_GREEN, PIN_BLUE
    PIN_RED = pin_red
    PIN_GREEN = pin_green
    PIN_BLUE = pin_blue

    pi.set_PWM_frequency(PIN_RED, 10_000)
    pi.set_PWM_frequency(PIN_GREEN, 10_000)
    pi.set_PWM_frequency(PIN_BLUE, 10_000)


def color(r, g, b):
    if any([r < 1, g < 1, b < 1]):
        r *= 255
        g *= 255
        b *= 255
    pi.set_PWM_dutycycle(PIN_GREEN, g)
    pi.set_PWM_dutycycle(PIN_RED, r)
    pi.set_PWM_dutycycle(PIN_BLUE, b)


def color_named(name):
    names = {
        "red": (0.8, 0, 0),
        "green": (0, 0.8, 0),
        "blue": (0, 0, 1),
        "violet": (1, 0, 1),
        "pink": (0.8, 0, 0.1),
        "rose": (1, 0.1, 0.1),
        "lightblue": (0, 0.2, 0.1),
        "lightrose": (0.1, 0.01, 0.01),
        "steelblue": (0.8, 0.5, 1),
        "lightsteelblue": (0.1, 0.05, 0.1),
        "lime": (1, 1, 0),
    }
    color(*names.get(name, (0, 0, 0)))


def init():
    config = flask.current_app.config.get("ILLUMINATION")
    if not config or not config.get("pins") or flask.current_app.testing:
        return

    try:
        import pigpio
    except ModuleNotFoundError:
        return
    global pi
    pi = pigpio.pi()

    logging.getLogger(__name__).info("Init")
    setup(*config["pins"])

    flask.current_app.events.register(
        "motion_detected",
        lambda: color_named(config.get("color_motion_detected")),
    )
    flask.current_app.events.register(
        "motion_lost",
        lambda: color_named(config.get("color_motion_lost")),
    )
    flask.current_app.events.register(
        "route_coffee",
        lambda: color_named(config.get("color_route_coffee")),
    )
    flask.current_app.events.register(
        "route_welcome",
        lambda: color_named(config.get("color_route_welcome")),
    )
    flask.current_app.events.register(
        "facerecognition_face_detected",
        lambda: color_named(config.get("color_facerecognition_face_detected")),
    )
    flask.current_app.events.register(
        "facerecognition_face_lost",
        lambda: color_named(config.get("color_facerecognition_face_lost")),
    )


if __name__ == "__main__":
    import argparse

    import IPython

    parser = argparse.ArgumentParser()
    parser.add_argument("color", help="Color in RGB (0-1) or (0-255). E.g. 255 255 0")
    args = parser.parse_args()

    setup(16, 20, 21)
    color(*[float(i) for i in args.color.split(" ")])
    IPython.embed()
