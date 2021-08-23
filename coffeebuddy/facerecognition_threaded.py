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
            if tag:
                self.socketio.emit('card_connected', data=dict(tag=tag.hex()))


def start(socketio):
    global thread
    facelock.put(True)
    thread = ThreadedFaceRecognition(socketio)
    thread.start()


def resume():
    if not facelock.empty():
        facelock.get()
        facelock.task_done()


def pause():
    if facelock.empty():
        facelock.put(True)