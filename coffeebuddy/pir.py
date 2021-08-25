import logging
import threading
import time
import subprocess

import flask
import RPi.GPIO as GPIO


thread = None


class PirThread(threading.Thread):
    sensor_pin = 18

    def __init__(self, timedelta=10):
        super().__init__()
        self.timedelta = timedelta
        self.running = True

        GPIO.setup(self.sensor_pin, GPIO.IN)

    def run(self):
        if GPIO.input(self.sensor_pin) == GPIO.LOW:
            flask.g.events.fire('pir_motion_paused')
        while True:
            if self.running:
                if GPIO.input(self.sensor_pin) == GPIO.HIGH:
                    flask.g.events.fire('pir_motion_detected')
                    time.sleep(self.timedelta)
                    if GPIO.input(self.sensor_pin) == GPIO.LOW:
                        flask.g.events.fire('pir_motion_paused')
            time.sleep(0.1)


def resume():
    if thread:
        logging.getLogger(__name__).info('ThreadedFaceRecognition resumed.')
        thread.running = True


def pause():
    if thread:
        logging.getLogger(__name__).info('ThreadedFaceRecognition paused.')
        thread.running = False


def init():
    flask.g.events.register('route_welcome', resume)
    flask.g.events.register('route_notwelcome', pause)
    flask.g.events.register('pir_motion_detected', lambda: subprocess.run(['xset', 'dpms', 'force', 'on']))
    flask.g.events.register('pir_motion_paused', lambda: subprocess.run(['xset', 'dpms', 'force', 'off']))

    global thread
    thread = PirThread()
    thread.start()
