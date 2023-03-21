import itertools

import flask

from coffeebuddy.model import User


def init():
    @flask.current_app.route("/selectuser.html")
    def selectuser():
        return flask.render_template(
            "selectuser.html",
            users=itertools.groupby(
                User.query.filter(User.enabled).order_by(User.name).all(),
                key=lambda u: u.name[0].upper(),
            ),
        )
