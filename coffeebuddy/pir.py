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
        self.events = flask.current_app.events

        GPIO.setup(self.sensor_pin, GPIO.IN)

    def run(self):
        if GPIO.input(self.sensor_pin) == GPIO.LOW:
            self.events.fire('pir_motion_paused')
        while True:
            if self.running:
                if GPIO.input(self.sensor_pin) == GPIO.HIGH:
                    self.events.fire('pir_motion_detected')
                    time.sleep(self.timedelta)
                    if self.running and GPIO.input(self.sensor_pin) == GPIO.LOW:
                        self.events.fire('pir_motion_paused')
            time.sleep(0.1)


def resume():
    if thread:
        logging.getLogger(__name__).info('PIR resumed.')
        thread.running = True


def pause():
    if thread:
        logging.getLogger(__name__).info('PIR paused.')
        thread.running = False


def init():
    flask.current_app.events.register('route_welcome', resume)
    flask.current_app.events.register('route_notwelcome', pause)
    flask.current_app.events.register('pir_motion_detected', lambda: subprocess.run(['xset', 'dpms', 'force', 'on']))
    flask.current_app.events.register('pir_motion_paused', lambda: subprocess.run(['xset', 'dpms', 'force', 'off']))

    global thread
    thread = PirThread()
    thread.start()
