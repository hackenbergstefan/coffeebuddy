import logging
import queue
import threading

import flask

from coffeebuddy import facerecognition

facelock = queue.Queue(maxsize=1)
thread = None


class ThreadedFaceRecognition(threading.Thread, facerecognition.FaceRecognizer):
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


def resume():
    logging.getLogger(__name__).info('ThreadedFaceRecognition resumed.')
    if not facelock.empty():
        facelock.get()
        facelock.task_done()


def pause():
    logging.getLogger(__name__).info('ThreadedFaceRecognition paused.')
    if facelock.empty():
        facelock.put(True)


def init():
    if flask.g.app.testing:
        return

    if flask.g.app.config['FACERECOGNITION'] is True:
        start(flask.g.socketio)
        flask.g.events.register('pir_motion_detected', resume)
        flask.g.events.register('pir_motion_paused', pause)
        flask.g.events.register('route_welcome', resume)
        flask.g.events.register('route_notwelcome', pause)
        flask.g.events.register('route_coffee_capture', pause)
        flask.g.events.register('facerecognition_threaded_pause', pause)
        flask.g.events.register('facerecognition_threaded_resume', resume)
