"""
User related routes.
"""

import math

import flask
import flask_login
from flask import Blueprint
from sqlalchemy.exc import IntegrityError

from coffeebuddy.extensions import webex

from ...model import Pay, User, escapefromhex
from .. import require_tag

blueprint = Blueprint("user", __name__, template_folder="templates")


@blueprint.route("/edituser.html", methods=["GET", "POST"])
def edit_user():
    request = flask.request
    db = flask.current_app.db

    user: User = User.by_id(request.args.get("id"))
    if user is None:
        tag = escapefromhex(request.args["tag"])
        user = User.by_tag(tag) or User(tag=tag, name="", prename="")
        db.session.add(user)

    def post():
        old = user.serialize()
        try:
            user.tag = escapefromhex(request.form["tag"])
            user.tag2 = escapefromhex(request.form["tag2"])
            user.name = request.form["name"]
            user.prename = request.form["prename"]
            user.email = request.form["email"]
            user.option_oneswipe = request.form["option_oneswipe"] == "true"

            if flask_login.current_user.is_authenticated:
                user.enabled = request.form["enabled"] == "true"
                balance = float(request.form["balance"])
                if not math.isclose(balance, user.balance):
                    user.update_balance(balance)
            db.session.commit()
            return flask.jsonify(
                {key: (old[key], new) for key, new in user.serialize().items()}
            )
        except IntegrityError as e:
            db.session.rollback()
            return flask.jsonify({"error": repr(e)})

    if request.method == "POST":
        return post()

    return flask.render_template(
        "edituser.html",
        user=user,
        flask_login=flask_login,
    )


@blueprint.route("/pay.html", methods=["GET", "POST"])
@require_tag
def pay(user: User):
    request = flask.request

    def post():
        db = flask.current_app.db
        amount = float(request.form["amount"])
        db.session.add(Pay(user=user, amount=amount))
        db.session.commit()

        webex.send_message(
            recipients=flask.current_app.config.get("PAYMENT_NOTIFICATION_EMAILS"),
            message=(
                f"{user} with balance of {user.balance - amount:.2f}€ "
                f"just entered a payment of **{amount:.2f}€**. "
                f"Their balance is now {user.balance:.2f}€."
            ),
        )

        return f"{user.balance:.2f}"

    if request.method == "POST":
        return post()

    return flask.render_template(
        "pay.html",
        user=User.by_tag(escapefromhex(request.args["tag"])),
    )


@blueprint.route("/stats.html")
@require_tag
def stats(user: User):
    return flask.render_template("stats.html", user=user)
