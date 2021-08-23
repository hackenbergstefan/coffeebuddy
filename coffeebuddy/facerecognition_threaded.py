import logging
import queue
import threading

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
            logging.getLogger(__name__).info(f'ThreadedFaceRecognition recognized {tag}.')
            if tag:
                self.socketio.emit('card_connected', data=dict(tag=tag.hex()))


def start(socketio):
    logging.getLogger(__name__).info('ThreadedFaceRecognition started.')
    global thread
    facelock.put(True)
    thread = ThreadedFaceRecognition(socketio)
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
