import logging
import threading
import time

try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    pass


thread = None


class PirThread(threading.Thread):
    sensor_pin = 18

    def __init__(self, callback_on, callback_off, timedelta=10):
        super().__init__()
        self.callback_on = callback_on
        self.callback_off = callback_off
        self.timedelta = timedelta
        self.running = True

        GPIO.setup(self.sensor_pin, GPIO.IN)

    def run(self):
        if GPIO.input(self.sensor_pin) == GPIO.LOW:
            self.callback_off()
        while True:
            if self.running:
                if GPIO.input(self.sensor_pin) == GPIO.HIGH:
                    self.callback_on()
                    time.sleep(self.timedelta)
                    if GPIO.input(self.sensor_pin) == GPIO.LOW:
                        self.callback_off()
            time.sleep(0.1)


def start(*args, **kwargs):
    logging.getLogger(__name__).info('ThreadedFaceRecognition started.')
    global thread
    thread = PirThread(*args, **kwargs)
    thread.start()


def resume():
    logging.getLogger(__name__).info('ThreadedFaceRecognition resumed.')
    thread.running = True


def pause():
    logging.getLogger(__name__).info('ThreadedFaceRecognition paused.')
    thread.running = False
