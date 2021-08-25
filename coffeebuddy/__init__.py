import datetime
import os
import random

import flask
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from sqlalchemy.exc import OperationalError

db = SQLAlchemy()

import coffeebuddy.events
import coffeebuddy.model  # noqa: E402
import coffeebuddy.routes
import coffeebuddy.attachments
import coffeebuddy.card
import coffeebuddy.facerecognition
import coffeebuddy.facerecognition_threaded


def create_app(config=None):
    app = Flask('coffeebuddy')
    socketio = SocketIO(app)

    app.config.from_object('config')
    # app.config['SQLALCHEMY_ECHO'] = True
    if config:
        app.config.update(config)

    if app.config['ENV'] in ('development', 'prefilled') or app.testing:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config.pop('SQLALCHEMY_DATABASE_URI', None)
        app.config.pop('SQLALCHEMY_ENGINE_OPTIONS', None)

    @app.teardown_appcontext
    def teardown_db(exception):
        db = flask.g.pop('db', None)
        if db is not None:
            db.session.close()

    return app, socketio


def init_db():
    db.init_app(flask.g.app)

    if (flask.g.app.config['ENV'] == 'sqlite' and not os.path.exists('coffee.db')) or \
       flask.g.app.config['ENV'] in ('development', 'prefilled') or \
       flask.g.app.testing:
        try:
            db.create_all()
        except OperationalError:
            # probably cannot connect to or init database
            os._exit(1)

    # Default database content
    if flask.g.app.config['ENV'] == 'development':
        db.session.add(coffeebuddy.model.User(tag=bytes.fromhex('01020304'), name='Mustermann', prename='Max'))
        db.session.commit()
    elif flask.g.app.config['ENV'] == 'prefilled':
        flask.g.app.debug = True
        prefill(db)

    return db


def init_routes():
    @flask.g.app.context_processor
    def inject_globals():
        return {
            'len': len,
            'round': round,
            'max': max,
            'min': min,
            'hexstr': lambda data: ' '.join(f'{x:02x}' for x in data),
        }
    coffeebuddy.routes.init()


def init_app_context(app, socketio):
    flask.g.events = coffeebuddy.events.EventManager()
    flask.g.db = db
    flask.g.app = app
    flask.g.socketio = socketio
    init_db()
    init_routes()
    coffeebuddy.attachments.init()
    coffeebuddy.card.init()
    coffeebuddy.facerecognition_threaded.init()
    coffeebuddy.facerecognition.init()


def prefill(db):
    demousers = [
        {'prename': 'Donald', 'postname': 'Duck', 'oneswipe': True},
        {'prename': 'Dagobert', 'postname': 'Duck', 'oneswipe': False},
        {'prename': 'Gyro', 'postname': ' Gearloose', 'oneswipe': False},
        {'prename': 'Tick ', 'postname': 'Duck', 'oneswipe': False},
        {'prename': 'Trick', 'postname': 'Duck', 'oneswipe': False},
        {'prename': 'Truck', 'postname': 'Duck', 'oneswipe': False},
    ]
    for idx, data in enumerate(demousers):
        db.session.add(coffeebuddy.model.User(
            tag=idx.to_bytes(1, 'big'),
            name=data['postname'],
            prename=data['prename'],
            option_oneswipe=data['oneswipe'],
        ))
    for _ in range(1000):
        db.session.add(coffeebuddy.model.Drink(
            userid=random.randint(0, len(demousers)),
            price=flask.g.app.config['PRICE'],
            timestamp=datetime.datetime.now() - datetime.timedelta(
                seconds=random.randint(0, 365 * 24 * 60 * 60)
            )
        ))
    db.session.commit()
