import logging
import subprocess

import flask


def init():
    logging.getLogger(__name__).info('Init')
    if flask.current_app.testing:
        return
    try:
        import RPi.GPIO as GPIO
    except ModuleNotFoundError:
        return

    if flask.current_app.config['PIR'] is None:
        return

    GPIO.setmode(GPIO.BCM)
    pin = flask.current_app.config['PIR']
    GPIO.setup(pin, GPIO.IN)

    GPIO.add_event_detect(pin, GPIO.RISING, callback=lambda _: flask.current_app.events.fire('pir_motion_detected'))
    GPIO.add_event_detect(pin, GPIO.FALLING, callback=lambda _: flask.current_app.events.fire('pir_motion_lost'))
    flask.current_app.events.register('pir_motion_detected', lambda: subprocess.run(['xset', 'dpms', 'force', 'on']))
    flask.current_app.events.register('pir_motion_lost', lambda: subprocess.run(['xset', 'dpms', 'force', 'off']))
