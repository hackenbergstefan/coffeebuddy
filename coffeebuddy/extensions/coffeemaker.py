import asyncio
import logging
import random
import time
from pathlib import Path
from threading import Thread
from types import TracebackType
from typing import Self, Type

import flask
import yaml
from flask_socketio import SocketIO
from jura_ble import CoffeeProduct, JuraBle, Machine

from coffeebuddy.model import CoffeeVariant

"""
This extension connects to a coffee maker and brews coffee.
"""


class CoffeeMakerMock:
    def __init__(self, brew_time: float):
        super().__init__()
        self.brew_time = brew_time
        self.socketio: SocketIO = flask.current_app.socketio
        self.socketio.on_event("coffeemaker:brew", self.brew)
        self.socketio.on_event("coffeemaker:manage", self.manage)
        with (Path(__file__).parent / "coffee_facts.yml").open() as fp:
            self.coffee_facts = yaml.load(fp, Loader=yaml.FullLoader)["coffee"]

    def run(self):
        while True:
            pass

    def brew(self, data):
        if data == "start":
            flask.current_app.events.fire("coffeemaker:brew:start")
            print("brew", data)
            fact = random.choice(self.coffee_facts)
            self.socketio.emit("coffeemaker:brew", {"state": "started", "fact": fact})
            time.sleep(self.brew_time)
            self.socketio.emit("coffeemaker:brew", {"state": "finished"})
            flask.current_app.events.fire("coffeemaker:brew:stop")
        elif data == "abort":
            flask.current_app.events.fire("coffeemaker:brew:stop")
            print("brew abort!")

    def manage(self, data):
        match data:
            case "unlock":
                print("unlock")
            case "lock":
                print("lock")


class JuraBle2:
    @staticmethod
    async def create(**kwargs):
        return JuraBle2()

    def __init__(self):
        self.brewing = False

    async def __aenter__(self) -> Self:
        asyncio.sleep(0.5)
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException],
        exc_val: BaseException,
        exc_tb: TracebackType,
    ) -> None:
        pass

    async def brew_product(self, product):
        print("brew", product)
        self.brewing = True

        async def _brew():
            await asyncio.sleep(5)
            self.brewing = False

        asyncio.create_task(_brew())

    async def _heartbeat_periodic(self):
        while True:
            await asyncio.sleep(5)

    async def unlock_machine(self):
        pass

    async def lock_machine(self):
        pass

    async def product_progress(self):
        if self.brewing:
            return True
        return None


class JuraCoffeeMaker:
    def __init__(self, **kwargs):
        self.socketio = flask.current_app.socketio
        self.events = flask.current_app.events
        self.jura = asyncio.run(JuraBle2.create(**kwargs))
        self.machine = Machine("EF658S_C")
        self._brewing = False

        async def heartbeat():
            await self.jura._heartbeat_periodic()

        Thread(target=lambda: asyncio.run(heartbeat()), daemon=True).start()

    def brew(self, coffee: CoffeeVariant):
        Thread(target=lambda: asyncio.run(self._brew(coffee))).start()

    def brew_abort(self):
        self._brewing = False

    async def _brew(self, coffee: CoffeeVariant):
        self.events.fire("coffeemaker:brew:start")
        self._brewing = True
        coffee = CoffeeProduct(
            code=coffee.derived_from,
            name=coffee.name,
            strength=coffee.strength,
            grinder_ratio=coffee.grinder_ratio,
            water=coffee.water,
            temperature=coffee.temperature,
            water_bypass=coffee.bypass,
            milk_foam=coffee.milk_foam,
            milk=coffee.milk,
            milk_break=0,
            stroke=0,
            _props=self.machine.product_properties,
        )

        await self.jura.unlock_machine()
        await self.jura.brew_product(coffee)

        async def _brew():
            try:
                async with asyncio.timeout(2):
                    while self._brewing:
                        if await self.jura.product_progress() is None:
                            return
                        await asyncio.sleep(0.2)
            except asyncio.TimeoutError:
                raise Exception("Brewing timeout!")

        await _brew()

        if self._brewing:
            self.socketio.emit("coffeemaker:brew:finished")
            self._brewing = False
        self.events.fire("coffeemaker:brew:stop")
        await self.jura.lock_machine()


def init():
    logging.getLogger(__name__).info("Init")
    app = flask.current_app
    config = app.config.get("COFFEEMAKER", None) or {}

    if "mock" in config:
        CoffeeMakerMock(brew_time=config["mock"])
    elif "jura_ble" in config:
        config = config["jura_ble"]
        flask.current_app.coffeemaker = JuraCoffeeMaker()
