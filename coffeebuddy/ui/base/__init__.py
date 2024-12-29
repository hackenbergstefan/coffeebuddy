"""
Basic routes.
"""

import datetime
import socket

import flask
from flask import Blueprint

from ... import __version__
from ...model import Drink, User

blueprint = Blueprint("base", __name__, template_folder="templates")


@blueprint.route("/")
def welcome():
    data = [
        (amount, date if isinstance(date, str) else date.strftime("%Y-%m-%d"))
        for amount, date in Drink.drinks_vs_days(datetime.timedelta(weeks=12))
    ]
    return flask.render_template(
        "welcome.html",
        dataset=data,
        hostname=socket.gethostname(),
        version=__version__,
    )


@blueprint.route("/selectuser.html")
def selectuser():
    return flask.render_template(
        "selectuser.html",
        users=User.all_enabled(),
        top_manual_users=User.top_selected_manually(),
    )


@blueprint.after_request
def after_request(response):
    if flask.request.endpoint:
        if flask.request.endpoint == "base.welcome":
            flask.current_app.events.fire("route_welcome")
        elif flask.request.endpoint != "static":
            flask.current_app.events.fire("route_notwelcome")
    return response


@blueprint.errorhandler(Exception)
def route_error(exception):
    return flask.render_template("error.html", exception=exception), 400
