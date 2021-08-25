import datetime

import flask

from coffeebuddy.model import Drink


def init():
    @flask.current_app.route('/')
    def welcome():
        return flask.render_template(
            'welcome.html',
            dataset=Drink.drinks_vs_days(datetime.timedelta(weeks=12))
        )
