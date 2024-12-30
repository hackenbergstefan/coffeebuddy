import subprocess

import flask

"""
This extension turns the display on and off based on the motion sensor using
`xset dpms`.
"""


def init():
    app = flask.current_app
    if not app.config["DISPLAY_ON_OFF"] or app.testing:
        return

    app.events.register(
        "motion_detected",
        lambda: subprocess.check_call(["xset", "dpms", "force", "on"]),
    )
    app.events.register(
        "motion_lost",
        lambda: subprocess.check_call(["xset", "dpms", "force", "off"]),
    )
    app.events.fire("motion_detected")
