import logging
import threading

import flask


class PirThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.events = flask.current_app.events
        self.pin = flask.current_app.config["PIR"]
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
    logging.getLogger(__name__).info("Init")
    if flask.current_app.testing:
        return
    try:
        import RPi.GPIO  # noqa: F401 pylint: disable=unused-import
    except ModuleNotFoundError:
        return

    if flask.current_app.config["PIR"] is None:
        return

    thread = PirThread()
    thread.start()
