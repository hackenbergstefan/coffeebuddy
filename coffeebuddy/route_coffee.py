import datetime

import flask

from coffeebuddy.model import Drink, User, escapefromhex


def last_mondays(weeks=4):
    now = datetime.datetime.now().date()
    monday = now - datetime.timedelta(days=now.weekday())
    return [monday - datetime.timedelta(weeks=i) for i in range(weeks)]


def init():
    @flask.current_app.route("/coffee.html", methods=["GET", "POST"])
    def coffee():
        flask.current_app.events.fire("route_coffee")
        user: User = User.by_tag(escapefromhex(flask.request.args["tag"]))
        if user is None:
            return flask.render_template(
                "cardnotfound.html", uuid=flask.request.args["tag"]
            )
        if flask.request.method == "GET" and user.option_oneswipe:
            return flask.render_template("oneswipe.html", user=user)
        if flask.request.method == "POST":
            if "coffee" in flask.request.form:
                flask.current_app.db.session.add(
                    Drink(
                        user=user,
                        price=flask.current_app.config["PRICE"],
                        selected_manually="manually" in flask.request.args,
                    )
                )
                flask.current_app.db.session.commit()
            elif "pay" in flask.request.form:
                return flask.redirect(f'pay.html?tag={flask.request.args["tag"]}')
            elif "logout" in flask.request.form:
                return flask.redirect("/")
            elif "edituser" in flask.request.form:
                return flask.redirect(f'edituser.html?tag={flask.request.args["tag"]}')
            elif "stats" in flask.request.form:
                return flask.redirect(f'stats.html?tag={flask.request.args["tag"]}')
            elif "capture" in flask.request.form:
                if "notimeout" in flask.request.args:
                    flask.current_app.events.fire("route_coffee_capture", user=user)
                return flask.redirect(f"{flask.request.url}&notimeout")

        return flask.render_template(
            "coffee.html",
            user=user,
            referer=flask.request.form if flask.request.method == "POST" else [],
            today_name=datetime.datetime.now().strftime("%A"),
            datetime=datetime,
            last_mondays=last_mondays(),
        )
