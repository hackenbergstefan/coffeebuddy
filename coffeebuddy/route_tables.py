import datetime

import flask

from coffeebuddy.model import Drink, User, Pay


def init():
    @flask.current_app.route("/tables.html")
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
