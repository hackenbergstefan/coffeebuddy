import os

from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

app = None
db = SQLAlchemy()
socketio = None

import coffeetag.model  # noqa: E402
import coffeetag.routes  # noqa: E402


def create_app(config=None):
    global app, socketio
    app = Flask('coffeetag')
    socketio = SocketIO(app)

    app.config['PRICE'] = 0.30
    app.config['PAY'] = 10
    # app.config['SQLALCHEMY_ECHO'] = True
    if config:
        app.config.update(config)

    if app.config['ENV'] == 'development' or app.testing:
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
    coffeetag.routes.init_routes(app, socketio)

    if app.config['ENV'] == 'development' or app.testing:
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
        db.session.add(coffeetag.model.User(tag=bytes.fromhex('01020304'), name='Mustermann', prename='Max'))
        db.session.commit()
    elif app.config['ENV'] == 'production':
        if not os.path.exists('coffee.db'):
            db.create_all()

    app.db = db
    return db
