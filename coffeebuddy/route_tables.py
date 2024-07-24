import datetime
import json

import flask
import flask_login
import webexteamssdk

from coffeebuddy.model import Drink, Pay, User


def init():
    @flask.current_app.route("/tables.html")
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
                # pylint: disable=singleton-comparison
                for user in User.query.filter(User.enabled == False).all()  # noqa: E712
            ],
        )

    @flask.current_app.route("/table_data_messages")
    @flask_login.login_required
    def table_data_messages():
        api = webexteamssdk.WebexTeamsAPI(
            access_token=flask.current_app.config["WEBEX_ACCESS_TOKEN"]
        )
        coffeebuddy_email = api.people.me().emails[0]

        def generate(users):
            for user in users:
                if not user.email:
                    continue
                try:
                    for msg in api.messages.list_direct(personEmail=user.email):
                        yield (
                            json.dumps(
                                {
                                    "timestamp": str(msg.created),
                                    "name": user.name,
                                    "prename": user.prename,
                                    "direction": "out"
                                    if msg.personEmail == coffeebuddy_email
                                    else "in",
                                    "message": msg.html if msg.html else msg.text,
                                }
                            ).encode()
                            + b"\n"
                        )
                except webexteamssdk.ApiError:
                    pass

        return flask.current_app.response_class(
            generate(User.query.filter(User.enabled).all()),
            mimetype="application/json",
        )
