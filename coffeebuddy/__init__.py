import datetime
import os
import random

from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

app = None
db = SQLAlchemy()
socketio = None

import coffeebuddy.model  # noqa: E402
import coffeebuddy.routes  # noqa: E402


def create_app(config=None):
    global app, socketio
    app = Flask('coffeebuddy')
    socketio = SocketIO(app)

    app.config.from_object('config')
    # app.config['SQLALCHEMY_ECHO'] = True
    if config:
        app.config.update(config)

    if app.config['ENV'] in ('development', 'prefilled') or app.testing:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///coffee.db'

    @app.teardown_appcontext
    def teardown_db(exception):
        db = g.pop('db', None)
        if db is not None:
            db.session.close()

    return app, socketio


def init_db(app):
    db.init_app(app)
    coffeebuddy.routes.init_routes(app, socketio)

    if app.config['ENV'] in ('development', 'prefilled') or app.testing:
        db.create_all()

    @app.context_processor
    def inject_globals():
        return {
            'len': len,
            'round': round,
            'max': max,
            'min': min,
            'hexstr': lambda data: ' '.join(f'{x:02x}' for x in data),
        }

    # Default database content
    if app.config['ENV'] == 'development':
        db.session.add(coffeebuddy.model.User(tag=bytes.fromhex('01020304'), name='Mustermann', prename='Max'))
        db.session.commit()
    elif app.config['ENV'] == 'production':
        if not os.path.exists('coffee.db'):
            db.create_all()
    elif app.config['ENV'] == 'prefilled':
        app.debug = True
        prefill(db)

    app.db = db
    return db


def prefill(db):
    demousers = [
        'Donald Duck',
        'Dagobert Duck',
        'Gyro Gearloose',
        'Tick Duck',
        'Trick Duck',
        'Truck Duck',
    ]
    for idx, name in enumerate(demousers):
        db.session.add(coffeebuddy.model.User(
            tag=idx.to_bytes(1, 'big'),
            name=name.split(' ')[1],
            prename=name.split(' ')[0],
        ))
    for _ in range(1000):
        db.session.add(coffeebuddy.model.Drink(
            userid=random.randint(0, len(demousers)),
            price=app.config['PRICE'],
            timestamp=datetime.datetime.now() - datetime.timedelta(
                seconds=random.randint(0, 365 * 24 * 60 * 60)
            )
        ))
    db.session.commit()
