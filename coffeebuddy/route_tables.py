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

    @flask.current_app.route("/api/<string:endpoint>", methods=["POST"])
    def api(endpoint: str):
        if endpoint == "get_users":
            return flask.jsonify(list(map(User.serialize, User.query.all())))
        elif endpoint == "set_user":
            data = flask.request.json
            if "id" not in data:
                flask.abort(400)
            user: User = User.query.filter(User.id == data["id"]).first()
            if not user:
                flask.abort(400)

            if "email" in data:
                user.email = data["email"]
            if "name" in data:
                user.name = data["name"]
            if "prename" in data:
                user.prename = data["prename"]
            if "tag" in data:
                user.tag = bytes.fromhex(data["tag"])
            if "tag2" in data:
                user.tag2 = bytes.fromhex(data["tag2"])
            flask.current_app.db.session.commit()
            return flask.jsonify(user.serialize())
        else:
            flask.abort(404)
