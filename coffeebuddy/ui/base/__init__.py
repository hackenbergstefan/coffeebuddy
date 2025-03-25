"""
Basic routes.
"""

import datetime
import socket
from pathlib import Path

import flask
from flask import Blueprint

from ... import __version__
from ...model import Drink, User

blueprint = Blueprint("base", __name__, template_folder="templates")


@blueprint.route("/")
def welcome():
    data = [
        (date if isinstance(date, str) else date.strftime("%Y-%m-%d"), amount)
        for date, amount in Drink.drinks_vs_days(datetime.timedelta(weeks=12))
    ]
    return flask.render_template(
        "welcome.html",
        dataset=data,
        hostname=socket.gethostname(),
        version=__version__,
        qrcode=(
            Path(__file__).parent.parent.parent / "static" / "qrhelp.svg"
        ).read_text(),
    )


@blueprint.route("/selectuser.html")
def selectuser():
    return flask.render_template(
        "selectuser.html",
        users=User.all_enabled(),
        top_manual_users=User.top_selected_manually(),
    )


@blueprint.errorhandler(Exception)
def route_error(exception):
    return flask.render_template("error.html", exception=exception), 400
