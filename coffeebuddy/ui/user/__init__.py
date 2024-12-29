"""
User related routes.
"""

import math

import flask
import flask_login
from flask import Blueprint

from ...model import Drink, Pay, User, escapefromhex
from .. import require_tag, url

blueprint = Blueprint("user", __name__, template_folder="templates")


@blueprint.route("/edituser.html", methods=["GET", "POST"])
def edit_user():
    request = flask.request
    db = flask.current_app.db

    user: User = User.by_id(request.args.get("id"))
    if user is None:
        tag = escapefromhex(request.args["tag"])
        user = User.by_tag(tag) or User(tag=tag, name="", prename="")
        db.session.add(user)

    def post():
        old = user.serialize()
        user.tag = escapefromhex(request.form["tag"])
        user.tag2 = escapefromhex(request.form["tag2"])
        user.name = request.form["last_name"]
        user.prename = request.form["first_name"]
        user.email = request.form["email"]
        user.option_oneswipe = "oneswipe" in request.form

        if flask_login.current_user.is_authenticated:
            user.enabled = "enabled" in request.form
            balance = float(request.form["balance"])
            if not math.isclose(balance, user.balance):
                user.update_balance(balance)
        db.session.commit()

        return flask.jsonify(
            {key: (old[key], new) for key, new in user.serialize().items()}
        )

    if request.method == "POST":
        return post()

    return flask.render_template(
        "edituser.html",
        user=user,
        flask_login=flask_login,
    )


@blueprint.route("/pay.html", methods=["GET", "POST"])
@require_tag
def pay(user: User):
    request = flask.request

    def post():
        db = flask.current_app.db
        amount = float(request.form["amount"])
        db.session.add(Pay(user=user, amount=amount))
        db.session.commit()
        return f"{user.balance:.2f}"

    if request.method == "POST":
        return post()

    return flask.render_template(
        "pay.html",
        user=User.by_tag(escapefromhex(request.args["tag"])),
    )


@blueprint.route("/stats.html")
@require_tag
def stats(user: User):
    return flask.render_template("stats.html", user=user)


# WEBEX_ACCESS_TOKEN = flask.current_app.config.get("WEBEX_ACCESS_TOKEN")
# if WEBEX_ACCESS_TOKEN:
#     api = webexteamssdk.WebexTeamsAPI(access_token=WEBEX_ACCESS_TOKEN)
# payment_notification_emails = flask.current_app.config.get(
#     "PAYMENT_NOTIFICATION_EMAILS"
# )

# for payment_notification_email in payment_notification_emails:
#     message_md = (
#         f"{user} with bill of {user.unpayed + amount:.2f}€ "
#         f"just entered a payment of **{amount:.2f}€**. "
#         f"Their bill is now {user.unpayed:.2f}€."
#     )
#     try:
#         # pylint: disable=possibly-used-before-assignment
#         api.messages.create(
#             toPersonEmail=payment_notification_email, markdown=message_md
#         )
#     except webexteamssdk.ApiError:
#         logging.getLogger(__name__).exception(
#             f"Could not send webex message for email={payment_notification_email}"
#         )
