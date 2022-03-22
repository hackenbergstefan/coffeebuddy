import math

import flask

from coffeebuddy.model import Drink, User


def handle_post():
    user = User.query.filter(
        (User.tag == bytes.fromhex(flask.request.form["oldtag"]))
        | (User.tag2 == bytes.fromhex(flask.request.form["oldtag2"]))
    ).first()
    if user is None:
        # Add new user
        user = User(
            tag=bytes.fromhex(flask.request.form["tag"]),
            tag2=bytes.fromhex(flask.request.form["tag2"]),
            name=flask.request.form["last_name"],
            prename=flask.request.form["first_name"],
            option_oneswipe="oneswipe" in flask.request.form,
        )
        flask.current_app.db.session.add(user)
        try:
            bill = float(flask.request.form["initial_bill"].replace(",", "."))
            for _ in range(math.ceil(bill / flask.current_app.config["PRICE"])):
                flask.current_app.db.session.add(Drink(user=user, price=flask.current_app.config["PRICE"]))
        except ValueError:
            pass
        flask.current_app.db.session.commit()
    else:
        # Edit existing new user
        user.tag = bytes.fromhex(flask.request.form["tag"])
        user.tag2 = bytes.fromhex(flask.request.form["tag2"])
        user.name = flask.request.form["last_name"]
        user.prename = flask.request.form["first_name"]
        user.option_oneswipe = "oneswipe" in flask.request.form
        flask.current_app.db.session.commit()
    return flask.redirect("/")


def handle_get():
    tag = bytes.fromhex(flask.request.args["tag"])
    return flask.render_template(
        "edituser.html",
        user=User.by_tag(tag) or User(tag=tag, name="", prename=""),
    )


def init():
    @flask.current_app.route("/edituser.html", methods=["GET", "POST"])
    def edit_user():
        if flask.request.method == "POST":
            return handle_post()
        elif flask.request.method == "GET":
            return handle_get()
        return flask.abort(404)
