"""
Coffee related routes.
"""

import random
from pathlib import Path

import flask
import yaml
from flask import Blueprint

from ...extensions.coffeemaker import JuraCoffeeMaker
from ...model import CoffeeVariant, Drink, User
from .. import require_coffeeid, require_tag, url

blueprint = Blueprint("coffee", __name__, template_folder="templates")

with (Path(__file__).parent / "../../extensions/sayings.yml").open() as fp:
    content = yaml.load(fp, Loader=yaml.FullLoader)
    coffee_facts = content["coffee"]
    clean_requests = content["clean"]


@blueprint.route("/coffee.html", methods=["GET", "POST"])
@require_tag
def coffee(user: User):
    request = flask.request

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
                url(
                    "brew.html",
                    tag=user.tag,
                    coffeeid=request.form["coffeeid"],
                    **{"manually": None} if "manually" in request.args else {},
                )
            )
        return flask.abort(404)

    if request.method == "POST":
        return post()

    has_coffeemaker = flask.current_app.config.get("COFFEEMAKER", None) is not None

    if (
        not has_coffeemaker
        and "can-oneswipe" in flask.request.args
        and user.option_oneswipe
    ):
        return flask.redirect(url("oneswipe.html", **flask.request.args))

    variants_favorites, variants = CoffeeVariant.all_for_user(user)
    return flask.render_template(
        "coffee.html",
        user=user,
        variants_favorites=variants_favorites,
        variants=variants,
        coffeemaker=has_coffeemaker,
        price=flask.current_app.config["PRICE"],
    )


@blueprint.route("/brew.html", methods=["GET", "POST"])
@require_tag
@require_coffeeid
def brew(user: User, coffee: CoffeeVariant):
    request = flask.request
    db = flask.current_app.db
    coffeemaker: JuraCoffeeMaker = flask.current_app.coffeemaker

    manually = {"manually": None} if "manually" in request.args else {}

    def post():
        if "start" in request.form:
            coffeemaker.brew(coffee)
            return ""
        elif "no" in request.form:
            return flask.redirect(url("coffee.html", tag=user.tag, **manually))
        elif "abort" in request.form:
            coffeemaker.brew_abort()
            return flask.redirect(url("coffee.html", tag=user.tag, **manually))
        elif "fav" in request.form:
            if coffee in user.variant_favorites:
                user.variant_favorites.remove(coffee)
            else:
                user.variant_favorites.append(coffee)
            db.session.commit()
            return flask.render_template(
                "brew.html",
                user=user,
                variant=coffee,
                fact=random.choice(coffee_facts),
            )
        elif "new" in request.form:
            return flask.redirect(
                url("editcoffee.html", tag=user.tag, derive=coffee.id, **manually)
            )
        elif "edit" in request.form:
            return flask.redirect(
                url("editcoffee.html", tag=user.tag, coffeeid=coffee.id, **manually)
            )
        elif "brewed" in request.form:
            if coffee.price > 0:
                db.session.add(
                    Drink(
                        user=user,
                        price=coffee.price,
                        coffeeid=coffee.id,
                        selected_manually="manually" in request.args,
                    )
                )
                db.session.commit()
            return flask.redirect(
                url(
                    "coffee.html",
                    tag=user.tag,
                    brewed=None,
                    **manually,
                )
            )

    if flask.request.method == "POST":
        return post()

    machine_status = flask.current_app.coffeemaker.machine_status()
    clean_reason = [
        alert for alert in ("cleaning alert", "decalc alert") if alert in machine_status
    ]
    return flask.render_template(
        "brew.html",
        user=user,
        variant=coffee,
        fact=random.choice(coffee_facts),
        clean_request=random.choice(clean_requests),
        clean_reason=clean_reason[0] if len(clean_reason) > 0 else None,
    )


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
            code=base_coffee.code,
            derived_from=base_coffee.id,
            icon=base_coffee.icon,
            strength=base_coffee.strength,
            grinder_ratio=base_coffee.grinder_ratio,
            water=base_coffee.water,
            temperature=base_coffee.temperature,
            bypass=base_coffee.bypass,
            milk_foam=base_coffee.milk_foam,
            milk=base_coffee.milk,
            price=base_coffee.price,
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
            | {"id": (coffee.id, coffee.id)}
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


@blueprint.route("/oneswipe.html", methods=["GET", "POST"])
@require_tag
def oneswipe(user: User):
    db = flask.current_app.db

    selected_manually = "manually" in flask.request.args

    if "coffee" in flask.request.form:
        db.session.add(
            Drink(
                user=user,
                price=flask.current_app.config["PRICE"],
                selected_manually=selected_manually,
            )
        )
        db.session.commit()
    elif "undo" in flask.request.form:
        return flask.redirect(
            url(
                "coffee.html",
                tag=user.tag,
                **{"manually": None} if selected_manually else {},
            )
        )
    return flask.render_template("oneswipe.html", user=user)


@blueprint.route("/coffee/manage.html", methods=["GET", "POST"])
def manage():
    def post():
        if "coffeemaker" in flask.request.form:
            coffeemaker = flask.current_app.coffeemaker
            match flask.request.form["coffeemaker"]:
                case "unlock":
                    coffeemaker.unlock_machine()
                    return ""
                case "lock":
                    coffeemaker.lock_machine()
                    return ""
                case "machine_status":
                    return flask.jsonify(coffeemaker.machine_status())
        return ""

    if flask.request.method == "POST":
        return post()
    return flask.render_template("manage.html")
