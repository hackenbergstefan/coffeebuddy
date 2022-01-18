#!/usr/bin/env python
import logging

import flask
import RPi.GPIO as GPIO


PIN_GREEN = 16
PIN_BLUE = 20
PIN_RED = 21

pwms = None


def setup():
    global pwms
    GPIO.setup(PIN_GREEN, GPIO.OUT)
    GPIO.setup(PIN_RED, GPIO.OUT)
    GPIO.setup(PIN_BLUE, GPIO.OUT)

    pwms = [
        GPIO.PWM(PIN_RED, 100),
        GPIO.PWM(PIN_GREEN, 100),
        GPIO.PWM(PIN_BLUE, 100),
    ]
    for p in pwms:
        p.start(1)


def color(r, g, b):
    if any([r > 1, g > 1, b > 1]):
        r /= 255
        g /= 255
        b /= 255
    if pwms:
        pwms[0].ChangeDutyCycle(100 * r)
        pwms[1].ChangeDutyCycle(100 * g)
        pwms[2].ChangeDutyCycle(100 * b)


def color_named(name):
    names = {
        'red': (0.8, 0, 0),
        'green': (0, 0.8, 0),
        'blue': (0, 0, 1),
        'violet': (1, 0, 1),
        'pink': (0.8, 0, 0.1),
        'lightblue': (0, 0.2, 0.1),
    }
    color(*names[name])


def init():
    logging.getLogger(__name__).info('Init')
    setup()

    flask.current_app.events.register('motion_detected', lambda: color_named('pink'))
    flask.current_app.events.register('motion_lost', lambda: color_named('lightblue'))
    flask.current_app.events.register('route_coffee', lambda: color_named('green'))
    flask.current_app.events.register('route_welcome', lambda: color_named('pink'))
    flask.current_app.events.register('facerecognition_face_detected', lambda: color_named('violet'))
    flask.current_app.events.register('facerecognition_face_lost', lambda: color_named('pink'))


if __name__ == '__main__':
    import IPython
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('color', help='Color in RGB (0-1) or (0-255). E.g. 255 255 0')
    args = parser.parse_args()

    setup()
    color(*[float(i) for i in args.color.split(' ')])
    IPython.embed()
    GPIO.cleanup()
