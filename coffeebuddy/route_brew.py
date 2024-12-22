import flask
from sqlalchemy import select

from coffeebuddy.model import CoffeeVariant, Drink, User, escapefromhex


def init():
    db = flask.current_app.db

    @flask.current_app.route("/brew.html", methods=["GET", "POST"])
    def brew():
        user: User = User.by_tag(escapefromhex(flask.request.args["tag"]))
        variant: CoffeeVariant = db.session.scalar(
            select(CoffeeVariant).where(
                CoffeeVariant.id == flask.request.args["coffeeid"]
            )
        )
        if flask.request.method == "POST":
            if "no" in flask.request.form:
                return flask.redirect(f'coffee.html?tag={flask.request.args["tag"]}')
            elif "abort" in flask.request.form:
                return flask.redirect(f'coffee.html?tag={flask.request.args["tag"]}')
            elif "fav" in flask.request.form:
                if variant in user.variant_favorites:
                    user.variant_favorites.remove(variant)
                else:
                    user.variant_favorites.append(variant)
                db.session.commit()
            elif "new" in flask.request.form:
                return flask.redirect(
                    f"editvariant.html?tag={user.tag.hex()}&derive={variant.id}"
                )
            elif "edit" in flask.request.form:
                return flask.redirect(
                    f"editvariant.html?tag={user.tag.hex()}&coffeeid={variant.id}"
                )
            elif "brewed" in flask.request.form:
                db.session.add(
                    Drink(
                        user=user,
                        price=flask.current_app.config["PRICE"],
                        coffeeid=variant.id,
                    )
                )
                db.session.commit()
                return flask.redirect(f'coffee.html?tag={flask.request.args["tag"]}')

        return flask.render_template("brew.html", user=user, variant=variant)
