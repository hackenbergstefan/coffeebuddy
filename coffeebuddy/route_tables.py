import datetime

import flask

from coffeebuddy.model import Drink, User, Pay


def init():
    @flask.current_app.route("/tables.html")
    def tables():
        return flask.render_template(
            "tables.html",
            bills=[(user.name, user.prename, round(user.unpayed, 2)) for user in User.query.all()],
            drinks=[
                (str(drink.timestamp), drink.user.name, drink.user.prename, drink.price)
                for drink in Drink.query.filter(
                    flask.current_app.db.func.Date(Drink.timestamp)
                    >= datetime.date.today() - datetime.timedelta(days=30)
                )
                if drink.user
            ]
            + [
                (str(pay.timestamp), pay.user.name, pay.user.prename, -pay.amount)
                for pay in Pay.query.all()
                if pay.user
            ],
        )
