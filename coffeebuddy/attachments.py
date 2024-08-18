import subprocess

import flask


def init():
    if flask.current_app.testing:
        return

    if flask.current_app.config["ILLUMINATION"]:
        import coffeebuddy.illumination

        coffeebuddy.illumination.init()

    if flask.current_app.config["MOTION_DISPLAY_CONTROL"] is True:
        flask.current_app.events.register(
            "motion_detected",
            lambda: subprocess.check_call(["xset", "dpms", "force", "on"]),
        )
        flask.current_app.events.register(
            "motion_lost",
            lambda: subprocess.check_call(["xset", "dpms", "force", "off"]),
        )
        flask.current_app.events.fire("motion_detected")
