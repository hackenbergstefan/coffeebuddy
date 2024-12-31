import datetime
import os
import random
from pathlib import Path

import flask
from sqlalchemy.exc import OperationalError


def prefill_users():
    from coffeebuddy.model import Drink, User

    db = flask.current_app.db

    demousers = [
        {
            "prename": "Donald",
            "postname": "Duck",
            "email": "donald.duck@entenhausen.com",
            "oneswipe": True,
        },
        {
            "prename": "Dagobert",
            "postname": "Duck",
            "email": "dagobert.duck@entenhausen.com",
            "oneswipe": False,
        },
        {
            "prename": "Gyro",
            "postname": " Gearloose",
            "email": "gyro.gearloose@entenhausen.com",
            "oneswipe": False,
        },
        {
            "prename": "Tick ",
            "postname": "Duck",
            "email": "tick.duck@entenhausen.com",
            "oneswipe": False,
        },
        {
            "prename": "Trick",
            "postname": "Duck",
            "email": "trick.duck@entenhausen.com",
            "oneswipe": False,
        },
        {
            "prename": "Truck",
            "postname": "Duck",
            "email": "truck.duck@entenhausen.com",
            "oneswipe": False,
        },
    ]
    for idx, data in enumerate(demousers):
        db.session.add(
            User(
                tag=idx.to_bytes(1, "big"),
                name=data["postname"],
                prename=data["prename"],
                email=data["email"],
                option_oneswipe=data["oneswipe"],
            )
        )
    for _ in range(1000):
        db.session.add(
            Drink(
                userid=random.randint(0, len(demousers)),
                price=flask.current_app.config["PRICE"],
                timestamp=datetime.datetime.now()
                - datetime.timedelta(seconds=random.randint(0, 365 * 24 * 60 * 60)),
                selected_manually=random.randint(0, 1),
            )
        )

    # Add guest user if not already present
    if flask.current_app.config["GUEST"]:
        if not User.query.filter(User.name == "Guest").first():
            db.session.add(User(tag=b"\xff\xff\xff\xff", name="Guest", prename=""))
            db.session.commit()


def prefill_coffee_variants():
    import xml.etree.ElementTree as ET

    from coffeebuddy.model import CoffeeVariant

    db = flask.current_app.db

    tree = ET.parse(Path(__file__).parent / "8xc_pro_1.0.xml")
    for product in tree.findall(".//{*}PRODUCT"):
        if product.attrib["DoubleProduct"] == "true":
            continue
        settings = {
            name: int(item.attrib.get("Value", 0) or item.attrib.get("Default", 0))
            if (item := product.find(f"{{*}}{setting.xml_name}")) is not None
            else 0
            for name, setting in CoffeeVariant.settings.items()
        }
        icon = {
            "espresso_1": "espresso",
            "ristretto_1": "espresso",
            "kaffee_1": "coffee",
            "cappuccino_1": "cappuccino",
            "milchkaffee_1": "flat-white",
            "latte_macchiato_1": "latte-macchiato",
            "latte_macchiato_long_1": "latte-macchiato",
            "milchschaum_long_1": "latte-macchiato",
            "milchportion_long_1": "latte-macchiato",
            "espresso_macchiato_1": "espresso-macchiato",
        }.get(product.attrib["PictureIdle"].replace(".png", ""), None)
        if not icon:
            continue

        variant = CoffeeVariant(
            name=product.attrib["Name"],
            icon=icon,
            editable=False,
            **settings,
        )
        db.session.add(variant)

    db.session.commit()


def init():
    app = flask.current_app
    prefilled = app.config.get("PREFILLED")

    if not prefilled and not app.testing:
        return

    # Create tables
    try:
        flask.current_app.db.drop_all()
        flask.current_app.db.create_all()
    except OperationalError:
        # probably cannot connect to or init database
        os._exit(1)

    prefill_users()
    prefill_coffee_variants()
