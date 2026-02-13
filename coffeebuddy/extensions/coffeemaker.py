import asyncio
import logging
import queue
from pathlib import Path
from threading import Thread

import flask

try:
    from jura_ble import CoffeeProduct, JuraBle, Machine, ProductProgressState
    from jura_ble.mock import JuraBleMock
except ImportError:
    pass

from coffeebuddy.model import CoffeeVariant

"""
This extension connects to a coffee maker and brews coffee.
"""


class JuraCoffeeMaker(Thread):
    def __init__(
        self,
        model: str,
        address: str,
        brew_timeout: float = 240,
        is_mock: bool = False,
        brew_time: float = 10,
    ):
        self.socketio = flask.current_app.socketio
        self.events = flask.current_app.events
        self.model = model
        self.address = address
        self.is_mock = is_mock
        self.brew_time = brew_time
        self.brew_timeout = brew_timeout
        self._brewing = False
        self.queue_in = queue.Queue()
        self.queue_out = queue.Queue()

        super().__init__(daemon=True)

    def run(self):
        asyncio.run(self._run())

    async def _run(self):
        while True:
            try:
                if self.is_mock:
                    self.jura = await JuraBleMock.create(model=self.model)
                else:
                    self.jura = await JuraBle.create(
                        model=self.model, address=self.address
                    )
                async with self.jura:
                    while True:
                        try:
                            method, data = self.queue_in.get_nowait()
                        except queue.Empty:
                            await asyncio.sleep(0.3)
                            continue
                        if method == "brew":
                            await self._brew(**data)
                        else:
                            result = await getattr(self.jura, method)(**data)
                            if result is not None:
                                self.queue_out.put(result)
            except Exception as e:
                logging.getLogger(__name__).error(e)
                self.socketio.emit("error", data=str(e))
                await asyncio.sleep(5)

    def brew_abort(self):
        self._brewing = False

    def machine_status(self, timeout: float = 2.0) -> list[str]:
        self.queue_in.put_nowait(("machine_status", {}))
        try:
            return self.queue_out.get(timeout=timeout)
        except queue.Empty:
            return ["error"]

    def lock_machine(self):
        self.queue_in.put_nowait(("lock_machine", {}))

    def unlock_machine(self):
        self.queue_in.put_nowait(("unlock_machine", {}))

    def brew(self, coffee: CoffeeVariant):
        self.queue_in.put_nowait(("brew", {"coffee": coffee}))

    async def _brew(self, coffee: CoffeeVariant):
        self.events.fire("coffeemaker:brew:start")
        self._brewing = True
        coffee = CoffeeProduct(
            code=coffee.code,
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
            _props=self.jura.model.product_properties,
        )

        await self.jura.unlock_machine()
        await self.jura.brew_product(coffee)

        async def _brew():
            try:
                async with asyncio.timeout(self.brew_timeout):
                    while self._brewing:
                        progress = await self.jura.product_progress()
                        logging.getLogger(__name__).debug(f"Progress: {progress}")
                        if (
                            progress.state
                            == ProductProgressState.LAST_PROGRESS_STATE
                        ):
                            return
                        await asyncio.sleep(0.5)
            except asyncio.TimeoutError:
                raise Exception("Brewing timeout!")

        if not self.is_mock:
            await _brew()
        else:
            await asyncio.sleep(self.brew_time)

        if self._brewing:
            self.socketio.emit("coffeemaker:brew:finished")
            self._brewing = False
        self.events.fire("coffeemaker:brew:stop")
        await self.jura.lock_machine()


def init():
    logging.getLogger(__name__).info("Init")
    app = flask.current_app
    config = app.config.get("COFFEEMAKER", {}) or {}

    if "jura_ble" in config:
        config = config["jura_ble"]
        flask.current_app.coffeemaker = JuraCoffeeMaker(
            model=config["model"],
            address=config["address"],
        )
        flask.current_app.coffeemaker.start()
    elif "jura_ble_mock" in config:
        config = config["jura_ble_mock"]
        flask.current_app.coffeemaker = JuraCoffeeMaker(
            model=config["model"],
            brew_time=config.get("brew_time", 10),
            address=None,
            is_mock=True,
        )
        flask.current_app.coffeemaker.start()

    if config != {} and app.config.get("PREFILLED"):
        prefill_coffee_variants()


def prefill_coffee_variants():
    db = flask.current_app.db
    coffeemaker = flask.current_app.coffeemaker
    products = Machine(coffeemaker.model).products
    icons = list(
        sorted(
            [
                icon.stem.replace("icon_", "").replace("_", " ")
                for icon in (Path(__file__).parent.parent / "static").glob("icon_*.svg")
            ],
            key=lambda n: len(n),
            reverse=True,
        )
    )
    for product in products:
        try:
            icon = next(i for i in icons if i in product.name.lower())
        except StopIteration:
            icon = ""
        db.session.add(
            CoffeeVariant(
                name=product.name,
                code=product.code,
                icon=icon.replace(" ", "-"),
                strength=product.strength,
                grinder_ratio=product.grinder_ratio,
                water=product.water,
                temperature=product.temperature,
                bypass=product.water_bypass,
                milk_foam=product.milk_foam,
                milk=product.milk,
                price=0.0
                if "water" in product.name
                else flask.current_app.config["PRICE"],
            )
        )
    for price in flask.current_app.config.get("PRICES_CHARGE_ONLY", []):
        db.session.add(
            CoffeeVariant(
                name=f"Charge {price:.2f}€",
                code=-1,
                icon="coffee",
                strength=0,
                grinder_ratio=0,
                water=0,
                temperature=0,
                bypass=0,
                milk_foam=0,
                milk=0,
                price=price,
            )
        )

    db.session.commit()
