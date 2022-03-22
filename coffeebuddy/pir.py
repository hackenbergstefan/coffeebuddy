import logging
import threading

import flask


class PirThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.events = flask.current_app.events
        self.pin = flask.current_app.config["PIR"]
        import RPi.GPIO as GPIO

        GPIO.setup(self.pin, GPIO.IN)

    def run(self):
        import RPi.GPIO as GPIO

        while True:
            GPIO.wait_for_edge(self.pin, GPIO.BOTH)
            self.events.fire("motion_detected" if GPIO.input(self.pin) else "motion_lost")


def init():
    logging.getLogger(__name__).info("Init")
    if flask.current_app.testing:
        return
    try:
        import RPi.GPIO  # noqa: F401
    except ModuleNotFoundError:
        return

    if flask.current_app.config["PIR"] is None:
        return

    thread = PirThread()
    thread.start()
