import math

import flask
import flask_login

from coffeebuddy.model import User, escapefromhex


def handle_post():
    try:
        userid = int(flask.request.form["id"])
    except ValueError:
        userid = None
    user = User.query.filter(User.id == userid).first()
    if user is None:
        # Add new User
        user = User(
            tag=escapefromhex(flask.request.form["tag"]),
            tag2=escapefromhex(flask.request.form["tag2"]),
            name=flask.request.form["last_name"],
            prename=flask.request.form["first_name"],
            email=flask.request.form["email"],
            option_oneswipe="oneswipe" in flask.request.form,
        )
        flask.current_app.db.session.add(user)
    else:
        # Edit existing User
        user.tag = escapefromhex(flask.request.form["tag"])
        user.tag2 = escapefromhex(flask.request.form["tag2"])
        user.name = flask.request.form["last_name"]
        user.prename = flask.request.form["first_name"]
        user.email = flask.request.form["email"]
        user.option_oneswipe = "oneswipe" in flask.request.form

    if flask_login.current_user.is_authenticated:
        user.enabled = "enabled" in flask.request.form
        unpayed = float(flask.request.form["unpayed"])
        if not math.isclose(unpayed, user.unpayed):
            user.update_bill(unpayed)

    flask.current_app.db.session.commit()


def handle_get():
    tag = escapefromhex(flask.request.args["tag"])
    return flask.render_template(
        "edituser.html",
        user=User.by_tag(tag) or User(tag=tag, name="", prename=""),
        flask_login=flask_login,
    )


def init():
    @flask.current_app.route("/edituser.html", methods=["GET", "POST"])
    def edit_user():
        if flask.request.method == "POST":
            return handle_post()
        if flask.request.method == "GET":
            return handle_get()
        return flask.abort(404)
