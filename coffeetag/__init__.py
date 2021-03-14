import importlib

from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy

app = None
db = SQLAlchemy()

import coffeetag.model
import coffeetag.routes


def create_app(config):
    global app
    app = Flask('coffeetag')
    app.config.update(config)
    if app.config['ENV'] == 'development' or app.testing:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
    # app.config['SQLALCHEMY_ECHO'] = True

    @app.teardown_appcontext
    def teardown_db(exception):
        db = g.pop('db', None)
        if db is not None:
            db.session.close()

    return app


def init_db(app):
    db.init_app(app)
    coffeetag.routes.init_routes(app)

    if app.config['ENV'] == 'development' or app.testing:
        db.drop_all()
        db.create_all()

    @app.context_processor
    def inject_globals():
        return {
            'len': len
        }

    return db
