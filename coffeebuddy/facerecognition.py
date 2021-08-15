import pickle
import threading

import cv2
import face_recognition

try:
    data = pickle.loads(open('face_encodings.pickle', 'rb').read())
except:
    data = {'encodings': [], 'names': []}


import queue
mylock = queue.Queue(maxsize=1)

face_found = False

def capture(name):
    global face_found
    face_found = False
    def click(event, x, y, flags, param):
        global face_found
        if face_found:
            return
        rgb, boxes, name = param
        # print(event, x, y, flags, param)
        if flags == cv2.EVENT_LBUTTONDOWN:
            print('save', name)
            for encoding in face_recognition.face_encodings(rgb, boxes):
                data['encodings'].append(encoding)
                data['names'].append(name)
            with open('face_encodings.pickle', 'wb') as fout:
                fout.write(pickle.dumps(data))
            face_found = True

    cap = cv2.VideoCapture(0)
    cap.set(3, 640) # set Width
    cap.set(4, 480) # set Height
    def _capture():
        while True:
            _, img = cap.read()
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(rgb, model='hog')

            for (y, xw, yh, x) in boxes:
                cv2.rectangle(img, (x, y), (xw, yh), (255, 0, 0), 2)

            cv2.imshow('video', img)
            cv2.setMouseCallback('video', click, (rgb, boxes, name))
            k = cv2.waitKey(50) & 0xff
            if k == 27 or face_found or cv2.getWindowProperty('video', cv2.WND_PROP_VISIBLE) < 1:
                return

    _capture()
    cap.release()
    cv2.destroyAllWindows()

class FaceDetection(threading.Thread):
    def __init__(self, socketio):
        super().__init__()
        self.socketio = socketio

    def run(self):
        while True:
            if not mylock.empty():
                mylock.join()
            name = self.detect()
            print(name)
            if name:
                self.socketio.emit('card_connected', data=dict(tag=name.hex()))

    def detect(self):
        cap = cv2.VideoCapture(0)
        cap.set(3, 640)
        cap.set(4, 480)
        _, img = cap.read()
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb, model='hog')

        for encoding in face_recognition.face_encodings(rgb, boxes):
            matches = face_recognition.compare_faces(data['encodings'], encoding)
            # print(encoding, matches)
            if True in matches:
                return data['names'][matches.index(True)]
        k = cv2.waitKey(30) & 0xff
        if k == 27: # press 'ESC' to quit
            return None
        cap.release()


def start(socketio):
    mylock.put(True)
    FaceDetection(socketio).start()


def pause():
    if mylock.empty():
        mylock.put(True)


def listen():
    if not mylock.empty():
        mylock.get()
        mylock.task_done()


def capture_locked(name):
    if not mylock.empty():
        pause()
    capture(name)
    if not mylock.empty():
        listen()


if __name__ == '__main__':
    pass
    # detect()
    # capture('sandra')
