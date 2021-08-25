import logging
import queue
import threading

import coffeebuddy.facerecognition
from coffeebuddy import app


facelock = queue.Queue(maxsize=1)
thread = None


class ThreadedFaceRecognition(threading.Thread, coffeebuddy.facerecognition.FaceRecognizer):
    def __init__(self, socketio):
        super().__init__()
        self.socketio = socketio

    def run(self):
        while True:
            if not facelock.empty():
                facelock.join()
            tag = self.recognize_once()
            if tag:
                logging.getLogger(__name__).info(f'ThreadedFaceRecognition recognized {tag}.')
                self.socketio.emit('card_connected', data=dict(tag=tag.hex()))


def start(*args):
    logging.getLogger(__name__).info('ThreadedFaceRecognition started.')
    global thread
    facelock.put(True)
    thread = ThreadedFaceRecognition(*args)
    thread.start()


def resume(**kwargs):
    logging.getLogger(__name__).info('ThreadedFaceRecognition resumed.')
    if not facelock.empty():
        facelock.get()
        facelock.task_done()


def pause(**kwargs):
    logging.getLogger(__name__).info('ThreadedFaceRecognition paused.')
    if facelock.empty():
        facelock.put(True)


def init():
    if app.testing:
        return

    if app.config['FACERECOGNITION'] is True:
        start(app.socketio)
        app.events.register('pir_motion_detected', resume)
        app.events.register('pir_motion_paused', pause)
        app.events.register('route_welcome', resume)
        app.events.register('route_notwelcome', pause)
        app.events.register('route_coffee_capture', pause)
        app.events.register('facerecognition_threaded_pause', pause)
        app.events.register('facerecognition_threaded_resume', resume)
