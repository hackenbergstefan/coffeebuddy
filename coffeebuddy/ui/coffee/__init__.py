"""
Coffee related routes.
"""

import flask
from flask import Blueprint

from ...model import CoffeeVariant, Drink, User
from .. import require_coffeeid, require_tag, url

blueprint = Blueprint("coffee", __name__, template_folder="templates")


@blueprint.route("/coffee.html", methods=["GET", "POST"])
@require_tag
def coffee(user: User):
    request = flask.request
    flask.current_app.events.fire("route_coffee")

    def post():
        db = flask.current_app.db

        if "coffee" in request.form:
            db.session.add(
                Drink(
                    user=user,
                    price=flask.current_app.config["PRICE"],
                    selected_manually="manually" in request.args,
                )
            )
            db.session.commit()
            return ""
        elif "pay" in request.form:
            return flask.redirect(url("pay.html", tag=user.tag))
        elif "back" in request.form:
            return flask.redirect("/")
        elif "edituser" in request.form:
            return flask.redirect(url("edituser.html", id=user.id))
        elif "stats" in request.form:
            return flask.redirect(url("stats.html", tag=user.tag))
        elif "coffeeid" in request.form:
            return flask.redirect(
                url("brew.html", tag=user.tag, coffeeid=request.form["coffeeid"])
            )
        return flask.abort(404)

    if request.method == "POST":
        return post()

    variants_favorites, variants = CoffeeVariant.all_for_user(user)
    return flask.render_template(
        "coffee.html",
        user=user,
        variants_favorites=variants_favorites,
        variants=variants,
        coffeemaker=flask.current_app.config.get("COFFEEMAKER", False)
        or flask.current_app.config.get("COFFEEMAKER_MOCK_BREW_TIME", False)
        is not False,
        price=flask.current_app.config["PRICE"],
    )


@blueprint.route("/brew.html", methods=["GET", "POST"])
@require_tag
@require_coffeeid
def brew(user: User, coffee: CoffeeVariant):
    request = flask.request
    db = flask.current_app.db

    def post():
        if "no" in request.form:
            return flask.redirect(url("coffee.html", tag=user.tag))
        elif "abort" in request.form:
            return flask.redirect(url("coffee.html", tag=user.tag))
        elif "fav" in request.form:
            if coffee in user.variant_favorites:
                user.variant_favorites.remove(coffee)
            else:
                user.variant_favorites.append(coffee)
            db.session.commit()
        elif "new" in request.form:
            return flask.redirect(
                url("editcoffee.html", tag=user.tag, derive=coffee.id)
            )
        elif "edit" in request.form:
            return flask.redirect(
                url("editcoffee.html", tag=user.tag, coffeeid=coffee.id)
            )
        elif "brewed" in request.form:
            db.session.add(
                Drink(
                    user=user,
                    price=flask.current_app.config["PRICE"],
                    coffeeid=coffee.id,
                )
            )
            db.session.commit()
            return flask.redirect(url("coffee.html", tag=user.tag))

    if flask.request.method == "POST":
        return post()

    return flask.render_template("brew.html", user=user, variant=coffee)


@blueprint.route("/editcoffee.html", methods=["GET", "POST"])
@require_tag
def editcoffee(user: User):
    db = flask.current_app.db
    request = flask.request

    if "coffeeid" in request.args:
        coffee = CoffeeVariant.by_id(request.args["coffeeid"])
    elif "derive" in request.args:
        base_coffee = CoffeeVariant.by_id(request.args["derive"])
        coffee = CoffeeVariant(
            name=f"New {base_coffee.name}",
            derived_from=base_coffee.id,
            icon=base_coffee.icon,
            strength=base_coffee.strength,
            grinder_ratio=base_coffee.grinder_ratio,
            water=base_coffee.water,
            temperature=base_coffee.temperature,
            bypass=base_coffee.bypass,
            milk_foam=base_coffee.milk_foam,
            milk=base_coffee.milk,
            editable=True,
        )
        db.session.add(coffee)
        db.session.flush()
        coffee.name += f" {coffee.id}"
    else:
        return flask.abort(404)

    def post():
        if "delete" in request.form:
            coffee.deleted = True
            db.session.commit()
            return ""
        old = coffee.serialize()
        for key in request.form:
            setattr(coffee, key, request.form[key])
        db.session.commit()
        return flask.jsonify(
            {key: (old[key], new) for key, new in coffee.serialize().items()}
        )

    if request.method == "POST":
        return post()

    return flask.render_template(
        "editcoffee.html",
        user=user,
        variant=coffee,
        variant_json=coffee.serialize(),
        title_text=f'Edit "{coffee.name}"'
        if "coffeeid" in request.args
        else f"New {base_coffee.name}",
        is_new="derive" in request.args,
    )


@blueprint.route("/oneswipe.html", methods=["POST"])
@require_tag
def oneswipe(user: User):
    db = flask.current_app.db

    if "coffee" in flask.request.form:
        db.session.add(Drink(user=user, price=flask.current_app.config["PRICE"]))
        db.session.commit()
    return ""
