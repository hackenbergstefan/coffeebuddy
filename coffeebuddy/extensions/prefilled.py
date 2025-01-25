import datetime
import os
import random

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
