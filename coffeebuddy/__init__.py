import logging
import os
import socket

import flask
from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

__version__ = "2.1.2"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
# logging.getLogger("jura_ble").setLevel(logging.DEBUG)


class Base(DeclarativeBase):
    pass


def _read_config(app):
    if os.path.exists(f"config_{socket.gethostname()}.py"):
        logging.getLogger(__name__).info(
            f'Using config file "config_{socket.gethostname()}"'
        )
        app.config.from_object(f"config_{socket.gethostname()}")
    else:
        logging.getLogger(__name__).info('Using config file "config"')
        app.config.from_object("config")


def create_app(config=None) -> Flask:
    app = Flask("coffeebuddy", template_folder="ui/templates")
    app.socketio = SocketIO(app)

    _read_config(app)
    if config:
        app.config.update(config)

    @app.teardown_appcontext
    def teardown_db(_exception):
        flask.current_app.db.session.close()

    return app


def init_app_context(app):
    # Init database
    db = SQLAlchemy(model_class=Base)
    Base.query = db.session.query_property()
    flask.current_app.db = db
    import coffeebuddy.model  # noqa: E402

    db.init_app(app)

    # Init UI
    import coffeebuddy.ui  # noqa: E402

    coffeebuddy.ui.init()

    # Init extensions
    import coffeebuddy.extensions  # noqa: E402

    coffeebuddy.extensions.init()
