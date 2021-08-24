import datetime

import flask
from flask import render_template

from coffeebuddy.model import Drink


def init():
    @flask.g.app.route('/')
    def welcome():
        return render_template(
            'welcome.html',
            dataset=Drink.drinks_vs_days(datetime.timedelta(weeks=12))
        )
