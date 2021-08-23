import logging
import os
import pickle
import threading

import cv2
import face_recognition


face_cascade = cv2.CascadeClassifier(
    os.path.join(os.path.dirname(cv2.__file__), 'data', 'haarcascade_frontalface_default.xml')
)
"""OpenCV cascade for frontal face detection. Used for fast face detection."""

face_data_path = os.path.join(os.path.dirname(__file__), 'face_encodings.pickle')
"""Path to binary face data."""
try:
    face_data = pickle.loads(open(face_data_path, 'rb').read())
    """Binary data of captured faces."""
except:
    face_data = {}


def save_face_data():
    """Save (updated) captured faces."""
    with open(face_data_path, 'wb') as fout:
        fout.write(pickle.dumps(face_data))
    print(list(face_data.keys()))


def add_face_data(tag, name, prename, encoding):
    face_data[(tag, name, prename)] = encoding
    save_face_data()


def detect_faces(img):
    """Return boxes containing faces."""
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Detect the faces
    return face_cascade.detectMultiScale(gray, scaleFactor=2, minNeighbors=4)


def mark_faces(img, boxes, name=None):
    """Draw rectangles around given boxes."""
    for (x, y, w, h) in boxes:
        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
        if name:
            cv2.putText(img, name, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)


def every_nth(nth):
    """Helper to execute loop function only every nth iteration."""
    n = 0
    while True:
        yield n == 0
        n = (n + 1) % nth


def cv2_show_and_wait(img, timeout=30):
    """Show given image and wait."""
    cv2.imshow('img', img)
    k = cv2.waitKey(timeout) & 0xff
    # Stop if escape key is pressed
    if k == 27:
        return True
    return False


def encode_face(img):
    """
    Encode face for later recognition.
    NOTE: Only first detected face is returned.
    """
    img_small = cv2.resize(img, (0, 0), fx=0.5, fy=0.5)
    rgb = cv2.cvtColor(img_small, cv2.COLOR_BGR2RGB)
    boxes = face_recognition.face_locations(rgb, model='hog')
    encodings = face_recognition.face_encodings(rgb, boxes)
    if len(encodings) == 0:
        return None
    return encodings[0]


def recognize_face(encoding):
    """Return key if encoding can be recognized."""
    matches = face_recognition.compare_faces(list(face_data.values()), encoding)
    if True in matches:
        return list(face_data.keys())[matches.index(True)]
    return None


class FaceCapturer:
    flipped = True
    """If True image is rotated by 180 degrees depending on camera orientation."""

    def __init__(self, tag, name, prename):
        self.tag = tag
        self.name = name
        self.prename = prename
        self.capturing = False

    def capture(self):
        cap = cv2.VideoCapture(0)
        cap.set(3, 640)
        cap.set(4, 480) 

        self.capturing = True
        detected_faces = []
        for nth in every_nth(4):
            _, img = cap.read()
            # Rotate image if needed
            if self.flipped:
                img = cv2.flip(img, -1)
            if nth:
                # Detect faces only every nth frame
                detected_faces = detect_faces(img)
            mark_faces(img, detected_faces)

            # Wait until button is pressed
            cv2.setMouseCallback('img', self.cv2_click_callback, param=img)
            if not self.capturing or cv2_show_and_wait(img):
                break

        # Cleanup
        cap.release()
        cv2.destroyAllWindows()

    def cv2_click_callback(self, event, x, y, flags, img):
        """Encode and save captured face on click/touch event."""
        if not self.capturing:
            return
        
        encoded_face = encode_face(img)
        logging.getLogger(__name__).info(f'Encoded face: {encoded_face}')
        if encoded_face is not None:
            logging.getLogger(__name__).info(f'Save face: {self.tag} {self.name} {self.prename} {encoded_face}')
            add_face_data(self.tag, self.name, self.prename, encoded_face)
            self.capturing = False


class FaceRecognizer:
    flipped = True

    def recognize_guiloop(self):
        cap = cv2.VideoCapture(0)
        cap.set(3, 640)
        cap.set(4, 480) 

        detected_faces = []
        detected_name = None
        for nth in every_nth(32):
            _, img = cap.read()
            # Rotate image if needed
            if self.flipped:
                img = cv2.flip(img, -1)
            if nth:
                # Use fast detection for boxes
                detected_faces = detect_faces(img)
                if len(detected_faces) > 0:
                    # Recognize
                    encoding = encode_face(img)
                    if encoding is not None:
                        tag, name, detected_name = recognize_face(encoding)
            mark_faces(img, detected_faces, detected_name)

            # Wait until button is pressed
            if cv2_show_and_wait(img):
                break

        # Cleanup
        cap.release()
        cv2.destroyAllWindows()

    def recognize_once(self):
        tag = None
        cap = cv2.VideoCapture(0)
        cap.set(3, 640)
        cap.set(4, 480) 
        _, img = cap.read()
        # Rotate image if needed
        if self.flipped:
            img = cv2.flip(img, -1)
        # Use fast detection for boxes
        detected_faces = detect_faces(img)
        if len(detected_faces) > 0:
            # Recognize
            encoding = encode_face(img)
            if encoding is not None:
                tag, _, _ = recognize_face(encoding)
        cap.release()
        return tag

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('function', choices=['capture', 'recognize'])
    parser.add_argument('--data', nargs='+', default=None, required=False, help='Tuple (TAG, PRENAME, NAME) for function "capture"')
    args = parser.parse_args()

    print('face_data', list(face_data.keys()))

    if args.function == 'capture':
        tag = bytes.fromhex(args.data[0])
        prename = args.data[1]
        name = args.data[2]
        FaceCapturer(tag, name, prename).capture()
    elif args.function == 'recognize':
        FaceRecognizer().recognize_guiloop()


if __name__ == '__main__':
    main()