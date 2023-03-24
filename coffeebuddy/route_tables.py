import datetime
import itertools
import logging

import flask
import webexteamssdk

from coffeebuddy.model import Drink, User, Pay


def init():
    @flask.current_app.route("/tables.html")
    def tables():
        api = webexteamssdk.WebexTeamsAPI(access_token=flask.current_app.config["WEBEX_ACCESS_TOKEN"])
        coffebuddyEmail = api.people.me().emails[0]

        icon_out = '<i class="fa-solid fa-right-from-bracket"></i>'
        icon_in = '<i class="fa-solid fa-right-to-bracket color-berry"></i>'

        def get_messages(email: str):
            try:
                return list(api.messages.list_direct(personEmail=email))
            except webexteamssdk.ApiError:
                logging.getLogger(__name__).exception(f"Could not get webex messages for email={email}")
                return ()

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
            messages=list(
                itertools.chain.from_iterable(
                    (
                        {
                            "timestamp": message.created,
                            "name": user.name,
                            "prename": user.prename,
                            "email": user.email,
                            "direction": icon_out if message.personEmail == coffebuddyEmail else icon_in,
                            "message": message.text,
                        }
                        for message in get_messages(user.email)
                    )
                    for user in User.query.filter(User.enabled).all()
                )
            ),
        )
