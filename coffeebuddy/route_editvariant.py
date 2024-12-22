import flask
from sqlalchemy import select

from coffeebuddy.model import CoffeeVariant, Drink, User, escapefromhex


def init():
    db = flask.current_app.db

    @flask.current_app.route("/editvariant.html", methods=["GET", "POST"])
    def editvariant():
        user: User = User.by_tag(escapefromhex(flask.request.args["tag"]))
        if "coffeeid" in flask.request.args:
            variant: CoffeeVariant = db.session.scalar(
                select(CoffeeVariant).where(
                    CoffeeVariant.id == flask.request.args["coffeeid"]
                )
            )
        elif "derive" in flask.request.args:
            base_variant: CoffeeVariant = db.session.scalar(
                select(CoffeeVariant).where(
                    CoffeeVariant.id == flask.request.args["derive"]
                )
            )
            variant = CoffeeVariant(
                name=f"New {base_variant.name}",
                derived_from=base_variant.id,
                icon=base_variant.icon,
                strength=base_variant.strength,
                grinder_ratio=base_variant.grinder_ratio,
                water=base_variant.water,
                temperature=base_variant.temperature,
                bypass=base_variant.bypass,
                milk_foam=base_variant.milk_foam,
                milk=base_variant.milk,
                editable=True,
            )
            db.session.add(variant)
            db.session.flush()
            variant.name += f" {variant.id}"
        else:
            return flask.abort(404)
        if flask.request.method == "POST":
            old = variant.serialize()
            for key in flask.request.form:
                setattr(variant, key, flask.request.form[key])
            db.session.commit()
            return flask.jsonify(
                {key: (old[key], new) for key, new in variant.serialize().items()}
            )
        return flask.render_template(
            "editvariant.html",
            user=user,
            variant=variant,
            variant_json=variant.serialize(),
            title_text=f'Edit "{variant.name}"'
            if "coffeeid" in flask.request.args
            else f"New {base_variant.name}",
        )
