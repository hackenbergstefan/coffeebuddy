import datetime
import itertools
import logging

import flask
import flask_login
import webexteamssdk

from coffeebuddy.model import Drink, User, Pay


def init():
    @flask.current_app.route("/tables.html")
    @flask_login.login_required
    def tables():
        api = webexteamssdk.WebexTeamsAPI(access_token=flask.current_app.config["WEBEX_ACCESS_TOKEN"])
        coffeebuddy_email = api.people.me().emails[0]

        def get_messages(email: str):
            if not email:
                return ()
            try:
                return list(api.messages.list_direct(personEmail=email))
            except webexteamssdk.ApiError as error:
                if error.message == "Failed to get one on one conversation":
                    # no prior conversation yet
                    return ()
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
                # pylint: disable=singleton-comparison
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
                            "direction": "out" if message.personEmail == coffeebuddy_email else "in",
                            "message": message.text,
                        }
                        for message in get_messages(user.email)
                    )
                    for user in User.query.filter(User.enabled).all()
                )
            ),
        )
