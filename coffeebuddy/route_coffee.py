import flask

from coffeebuddy.model import CoffeeVariant, Drink, User, escapefromhex


def init():
    @flask.current_app.route("/coffee.html", methods=["GET", "POST"])
    def coffee():
        flask.current_app.events.fire("route_coffee")
        user: User = User.by_tag(escapefromhex(flask.request.args["tag"]))
        if user is None:
            return flask.render_template(
                "cardnotfound.html", uuid=flask.request.args["tag"]
            )
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
            elif "back" in flask.request.form:
                return flask.redirect("/")
            elif "edituser" in flask.request.form:
                return flask.redirect(f'edituser.html?tag={flask.request.args["tag"]}')
            elif "stats" in flask.request.form:
                return flask.redirect(f'stats.html?tag={flask.request.args["tag"]}')
            elif "coffeeid" in flask.request.form:
                return flask.redirect(
                    f'brew.html?tag={flask.request.args["tag"]}&coffeeid={flask.request.form["coffeeid"]}'
                )

        variants_favorites, variants = CoffeeVariant.all_for_user(user)
        return flask.render_template(
            "coffee.html",
            user=user,
            variants_favorites=variants_favorites,
            variants=variants,
            referer=flask.request.form if flask.request.method == "POST" else [],
        )
