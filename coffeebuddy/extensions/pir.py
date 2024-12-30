import logging
import threading

import flask

"""
This extension fires events when motion is detected using a PIR sensor.

Can be used to control the illumination or the display.
"""


class PirThread(threading.Thread):
    def __init__(self, pin):
        super().__init__()
        self.events = flask.current_app.events
        self.pin = pin
        from RPi import GPIO

        GPIO.setup(self.pin, GPIO.IN)

    def run(self):
        from RPi import GPIO

        while True:
            GPIO.wait_for_edge(self.pin, GPIO.BOTH)
            self.events.fire(
                "motion_detected" if GPIO.input(self.pin) else "motion_lost"
            )


def init():
    if flask.current_app.testing:
        return
    config = flask.current_app.config["PIR"]
    if not config:
        return
    try:
        import RPi.GPIO  # noqa: F401
    except ModuleNotFoundError:
        return
    logging.getLogger(__name__).info("Init")

    thread = PirThread(pin=config)
    thread.start()
