import datetime
import logging
import queue
import threading
import time

import flask

import coffeebuddy.facerecognition

cameralock = queue.Queue(maxsize=1)
thread = None  # pylint: disable=invalid-name


class CameraThread(threading.Thread, coffeebuddy.facerecognition.FaceRecognizer):
    def __init__(self):
        super().__init__()
        self.app_config = flask.current_app.config
        self.events = flask.current_app.events
        self.socketio = flask.current_app.socketio
        self.avgimage = None

    def motiondetected(self):
        import cv2

        cap = cv2.VideoCapture(0)
        cap.set(3, 320)
        cap.set(4, 240)
        _, img = cap.read()
        cap.release()
        grayimage = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        if self.avgimage is None:
            self.avgimage = grayimage.copy().astype("float")
        cv2.accumulateWeighted(grayimage, self.avgimage, 0.5)
        delta = cv2.absdiff(grayimage, cv2.convertScaleAbs(self.avgimage))
        delta = cv2.mean(delta)[0]
        if delta > self.app_config["CAMERA_MOTION_DELTA"]:
            return True
        return False

    def run(self):
        last_motion_detected = datetime.datetime.now()
        while True:
            if not cameralock.empty():
                cameralock.join()

            detected = self.motiondetected()
            if datetime.datetime.now() - last_motion_detected < datetime.timedelta(
                seconds=self.app_config["CAMERA_MOTION_WAIT"]
            ):
                tag = self.recognize_once()
                if tag:
                    logging.getLogger(__name__).info(f"Face recognized {tag}.")
                    self.socketio.emit("card_connected", data={"tag": tag.hex()})
            elif detected:
                last_motion_detected = datetime.datetime.now()
                self.events.fire_reset("motion_lost")
                self.events.fire("motion_detected")
                logging.getLogger(__name__).info(
                    f"Motion detected {last_motion_detected}."
                )
            else:
                self.events.fire_once("motion_lost")
            time.sleep(0.05)


def resume(**_kwargs):
    logging.getLogger(__name__).info("Camera resumed.")
    if not cameralock.empty():
        cameralock.get()
        cameralock.task_done()


def pause(**_kwargs):
    logging.getLogger(__name__).info("Camera paused.")
    if cameralock.empty():
        cameralock.put(True)


def init():
    if flask.current_app.testing:
        return

    if flask.current_app.config["CAMERA"] is True:
        import cv2

        logging.getLogger(__name__).info("Camera init.")
        if "CAMERA_MOTION_WAIT" not in flask.current_app.config:
            flask.current_app.config["CAMERA_MOTION_WAIT"] = 10
        if "CAMERA_MOTION_DELTA" not in flask.current_app.config:
            flask.current_app.config["CAMERA_MOTION_DELTA"] = 2

        if "CAMERA_ROTATION" in flask.current_app.config:
            if flask.current_app.config["CAMERA_ROTATION"] == 90:
                flask.current_app.config["CAMERA_ROTATION"] = cv2.ROTATE_90_CLOCKWISE
            elif flask.current_app.config["CAMERA_ROTATION"] == 180:
                flask.current_app.config["CAMERA_ROTATION"] = cv2.ROTATE_180
            elif flask.current_app.config["CAMERA_ROTATION"] == 270:
                flask.current_app.config["CAMERA_ROTATION"] = (
                    cv2.ROTATE_90_COUNTERCLOCKWISE
                )
        else:
            flask.current_app.config["CAMERA_ROTATION"] = None

        flask.current_app.events.register("route_welcome", resume)
        flask.current_app.events.register("route_notwelcome", pause)
        flask.current_app.events.register("facerecognition_capture", pause)
        flask.current_app.events.register("camera_pause", pause)
        flask.current_app.events.register("camera_resume", resume)

        global thread  # pylint: disable=global-statement
        cameralock.put(True)
        thread = CameraThread()
        thread.start()
