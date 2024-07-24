import datetime
import socket

import flask

import coffeebuddy
from coffeebuddy.model import Drink


def init():
    @flask.current_app.route("/")
    def welcome():
        data = [
            (amount, date if isinstance(date, str) else date.strftime("%Y-%m-%d"))
            for amount, date in Drink.drinks_vs_days(datetime.timedelta(weeks=12))
        ]
        return flask.render_template(
            "welcome.html",
            dataset=data,
            hostname=socket.gethostname(),
            version=coffeebuddy.__version__,
        )
