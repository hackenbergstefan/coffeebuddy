import datetime

import flask
from flask import render_template

from coffeebuddy.model import User, Drink


def init():
    @flask.g.app.route('/tables.html')
    def tables():
        return render_template(
            'tables.html',
            bills=[
                (user.name, user.prename, user.tag.hex(), round(user.unpayed, 2))
                for user in User.query.all()
            ],
            drinks=[
                (str(drink.timestamp), drink.user.name, drink.user.prename, drink.price)
                for drink in
                Drink.query.filter(flask.g.db.func.Date(Drink.timestamp) >= datetime.date.today() - datetime.timedelta(days=30))
                if drink.user
            ]
        )
