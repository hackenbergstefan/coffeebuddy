import flask

from coffeebuddy.model import Drink, User, escapefromhex


def init():
    @flask.current_app.route("/oneswipe.html", methods=["POST"])
    def oneswipe():
        user = User.by_tag(escapefromhex(flask.request.args["tag"]))
        if "coffee" in flask.request.form:
            flask.current_app.db.session.add(
                Drink(user=user, price=flask.current_app.config["PRICE"])
            )
            flask.current_app.db.session.commit()
        return ""
