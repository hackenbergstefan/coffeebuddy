import logging
import random
import time
from pathlib import Path

import flask
import yaml
from flask_socketio import SocketIO

"""
This extension connects to a coffee maker and brews coffee.
"""


class CoffeeMaker:
    def __init__(self):
        super().__init__()
        self.socketio: SocketIO = flask.current_app.socketio
        self.socketio.on_event("brew", self.brew)
        with (Path(__file__).parent / "coffee_facts.yml").open() as fp:
            self.coffee_facts = yaml.load(fp, Loader=yaml.FullLoader)["coffee"]

    def run(self):
        while True:
            pass

    def brew(self, data):
        print("brew", data)
        if data == "start":
            print("brew", data)
            fact = random.choice(self.coffee_facts)
            self.socketio.emit("brew", {"state": "started", "fact": fact})
            time.sleep(10)
            self.socketio.emit("brew", {"state": "finished"})
        elif data == "abort":
            print("brew abort!")


def init():
    logging.getLogger(__name__).info("Init")

    CoffeeMaker()
