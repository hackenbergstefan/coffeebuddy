import datetime
import dataclasses
import logging
import os
import random
import socket

import flask
import flask_login
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError


db = SQLAlchemy()
login_manager = flask_login.LoginManager()


@dataclasses.dataclass
class AdminUser(flask_login.UserMixin):
    user_id: str

    def get_id(self):
        return self.user_id


@login_manager.user_loader
def load_user(user_id):
    return AdminUser(user_id=user_id)


def create_app(config=None):
    app = Flask("coffeebuddy")
    app.socketio = SocketIO(app)

    if os.path.exists(f"config_{socket.gethostname()}.py"):
        logging.getLogger(__name__).info(f'Using config file "config_{socket.gethostname()}"')
        app.config.from_object(f"config_{socket.gethostname()}")
    else:
        logging.getLogger(__name__).info('Using config file "config"')
        app.config.from_object("config")
    # app.config['SQLALCHEMY_ECHO'] = True
    if config:
        app.config.update(config)

    if app.config["ENV"] in ("development", "prefilled") or app.testing:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    @app.teardown_appcontext
    def teardown_db(_exception):
        flask.current_app.db.session.close()

    login_manager.init_app(app)
    return app


def init_db(app):
    flask.g.db = flask.current_app.db = db
    import coffeebuddy.model  # noqa: E402

    flask.current_app.db.init_app(app)

    if (
        (flask.current_app.config["DB_BACKEND"] == "sqlite" and not os.path.exists("coffee.db"))
        or flask.current_app.config["ENV"] in ("development", "prefilled")
        or flask.current_app.testing
    ):
        try:
            flask.current_app.db.create_all()
        except OperationalError:
            # probably cannot connect to or init database
            os._exit(1)

    # Default database content
    if flask.current_app.config["ENV"] == "development":
        flask.current_app.db.session.add(
            coffeebuddy.model.User(tag=bytes.fromhex("01020304"), name="Mustermann", prename="Max")
        )
        flask.current_app.db.session.commit()
    elif flask.current_app.config["ENV"] == "prefilled":
        flask.current_app.debug = True
        prefill()

    if flask.current_app.config["GUEST"]:
        if not coffeebuddy.model.User.query.filter(coffeebuddy.model.User.name == "Guest").first():
            flask.current_app.db.session.add(coffeebuddy.model.User(tag=b"\xff\xff\xff\xff", name="Guest", prename=""))
            flask.current_app.db.session.commit()

    return flask.current_app.db


def init_app_context(app):
    init_db(app)

    import coffeebuddy.events  # noqa: E402

    flask.current_app.events = coffeebuddy.events.EventManager()

    import coffeebuddy.routes

    coffeebuddy.routes.init()

    import coffeebuddy.attachments

    coffeebuddy.attachments.init()
    import coffeebuddy.card

    coffeebuddy.card.init()
    import coffeebuddy.camera

    coffeebuddy.camera.init()
    import coffeebuddy.facerecognition

    coffeebuddy.facerecognition.init()

    import coffeebuddy.pir

    coffeebuddy.pir.init()

    if "REMINDER_MESSAGE" in flask.current_app.config:
        start_scheduler(app)


def prefill():
    import coffeebuddy.model

    demousers = [
        {"prename": "Donald", "postname": "Duck", "email": "donald.duck@entenhausen.com", "oneswipe": True},
        {"prename": "Dagobert", "postname": "Duck", "email": "dagobert.duck@entenhausen.com", "oneswipe": False},
        {"prename": "Gyro", "postname": " Gearloose", "email": "gyro.gearloose@entenhausen.com", "oneswipe": False},
        {"prename": "Tick ", "postname": "Duck", "email": "tick.duck@entenhausen.com", "oneswipe": False},
        {"prename": "Trick", "postname": "Duck", "email": "trick.duck@entenhausen.com", "oneswipe": False},
        {"prename": "Truck", "postname": "Duck", "email": "truck.duck@entenhausen.com", "oneswipe": False},
    ]
    for idx, data in enumerate(demousers):
        flask.current_app.db.session.add(
            coffeebuddy.model.User(
                tag=idx.to_bytes(1, "big"),
                name=data["postname"],
                prename=data["prename"],
                email=data["email"],
                option_oneswipe=data["oneswipe"],
            )
        )
    for _ in range(1000):
        flask.current_app.db.session.add(
            coffeebuddy.model.Drink(
                userid=random.randint(0, len(demousers)),
                price=flask.current_app.config["PRICE"],
                timestamp=datetime.datetime.now() - datetime.timedelta(seconds=random.randint(0, 365 * 24 * 60 * 60)),
            )
        )
    flask.current_app.db.session.commit()


def start_scheduler(app):
    from coffeebuddy.reminder import remind

    scheduler = BackgroundScheduler()
    scheduler.start()
    scheduler.add_job(
        func=remind,
        args=(app,),
        trigger="interval",
        minutes=60,
        id="webex dept reminder",
        name="webex dept reminder",
        replace_existing=True,
    )
