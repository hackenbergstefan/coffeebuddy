import logging

import flask
import webexteamssdk

from coffeebuddy.model import Pay, User, escapefromhex

WEBEX_ACCESS_TOKEN = flask.current_app.config.get("WEBEX_ACCESS_TOKEN")
if WEBEX_ACCESS_TOKEN:
    api = webexteamssdk.WebexTeamsAPI(access_token=WEBEX_ACCESS_TOKEN)
payment_notification_emails = flask.current_app.config.get(
    "PAYMENT_NOTIFICATION_EMAILS"
)


def handle_post():
    user = User.by_tag(escapefromhex(flask.request.args["tag"]))
    amount = int(flask.request.form["amount"])
    flask.current_app.db.session.add(Pay(user=user, amount=amount))
    flask.current_app.db.session.commit()

    for payment_notification_email in payment_notification_emails:
        message_md = (
            f"{user} with bill of {user.unpayed + amount:.2f}€ "
            f"just entered a payment of **{amount:.2f}€**. "
            f"Their bill is now {user.unpayed:.2f}€."
        )
        try:
            # pylint: disable=possibly-used-before-assignment
            api.messages.create(
                toPersonEmail=payment_notification_email, markdown=message_md
            )
        except webexteamssdk.ApiError:
            logging.getLogger(__name__).exception(
                f"Could not send webex message for email={payment_notification_email}"
            )

    return flask.redirect(f'coffee.html?tag={flask.request.args["tag"]}')
    # return flask.abort(404)


def handle_get():
    return flask.render_template(
        "pay.html",
        user=User.by_tag(escapefromhex(flask.request.args["tag"])),
    )


def init():
    @flask.current_app.route("/pay.html", methods=["GET", "POST"])
    def pay():
        if flask.request.method == "POST":
            return handle_post()
        if flask.request.method == "GET":
            return handle_get()
        return flask.abort(404)
