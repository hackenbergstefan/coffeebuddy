"""
Admin related routes.
"""

import datetime

import flask
import flask_login
from flask import Blueprint

from ... import AdminUser
from ...model import Drink, Pay, User

blueprint = Blueprint("admin", __name__, template_folder="templates")


@blueprint.route("/login.html", methods=["GET", "POST"])
def login():
    if not flask.current_app.config.get("ADMIN_PASSWORD"):
        return flask.abort(404)
    if flask.request.method == "POST":
        password = flask.request.form.get("password")
        if password == flask.current_app.config["ADMIN_PASSWORD"]:
            flask_login.login_user(AdminUser(user_id="admin"), remember=True)
            return flask.redirect("/tables.html")
    return flask.render_template("login.html")


@blueprint.route("/tables.html")
@flask_login.login_required
def tables():
    return flask.render_template(
        "tables.html",
        bills=[
            {
                "name": user.name,
                "prename": user.prename,
                "email": user.email,
                "bill": round(user.unpayed, 2),
                "tag": user.tag.hex(),
            }
            for user in User.query.filter(User.enabled).all()
        ],
        drinks=[
            {
                "timestamp": str(drink.timestamp),
                "name": drink.user.name,
                "prename": drink.user.prename,
                "email": drink.user.email,
                "price": drink.price,
            }
            for drink in Drink.query.filter(
                flask.current_app.db.func.Date(Drink.timestamp)
                >= datetime.date.today() - datetime.timedelta(days=30)
            )
            if drink.user
        ]
        + [
            {
                "timestamp": str(pay.timestamp),
                "name": pay.user.name,
                "prename": pay.user.prename,
                "email": pay.user.email,
                "price": -pay.amount,
            }
            for pay in Pay.query.all()
            if pay.user
        ],
        bills_disabled=[
            {
                "name": user.name,
                "prename": user.prename,
                "email": user.email,
                "bill": round(user.unpayed, 2),
                "tag": user.tag.hex(),
            }
            for user in User.query.filter(User.enabled == False).all()  # noqa: E712
        ],
    )
