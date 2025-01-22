import logging
import threading
import time

import flask

try:
    import spidev
except ImportError:
    pass


def flatten(xss):
    return [x for xs in xss for x in xs]


def rgb_to_bits(rgb: tuple[int, int, int]):
    r, g, b = rgb
    return flatten(
        (0xF8 if bit == "1" else 0xC0 for bit in f"{color:08b}") for color in (g, r, b)
    )


class PulsingTask(threading.Thread):
    def __init__(self, func, *args, **kwargs):
        self._running = False
        self._func = func
        super().__init__(*args, **kwargs)

    def start(self):
        self._running = True
        return super().start()

    def stop(self):
        self._running = False

    def run(self):
        while True:
            if self._running is False:
                return
            self._func()


class NeopixelSpi:
    instance = None

    def __init__(self, bus: int, device: int, leds: int, spi_freq=800):
        NeopixelSpi.instance = self
        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)
        self.spi.max_speed_hz = spi_freq * 1024 * 8

        self.state = leds * [(0, 0, 0)]
        self._pulse_task = None
        self._pulsing = False
        self.clear()

    def update(self):
        raw_data = sum((rgb_to_bits(led) for led in self.state), [])
        self.spi.xfer3(raw_data)

    def clear(self):
        self.pulse_stop()
        self.fill(0, 0, 0)

    def fill(self, red: int, green: int, blue: int):
        self.pulse_stop()
        self.state = len(self.state) * [(red % 256, green % 256, blue % 256)]
        self.update()

    def fade(self, color_from, color_to, duration=0.1, steps=20):
        for i in range(steps + 1):
            self.fill(
                *tuple(
                    round(c1 + (c2 - c1) / steps * i)
                    for c1, c2 in zip(color_from, color_to)
                )
            )
            time.sleep(duration / steps)

    def pulse_once(self, color, amplitude=1.0, duration=0.5, steps="auto"):
        if steps == "auto":
            steps = 20 * duration
        color_to = [(1 - amplitude) * c for c in color]
        self.fade(color, color_to, duration=duration / 2, steps=steps)
        self.fade(color_to, color, duration=duration / 2, steps=steps)

    def pulse(self, color, amplitude=1.0, duration=0.5, steps="auto"):
        self.pulse_stop()
        self._pulse_task = PulsingTask(
            func=lambda: self.pulse_once(
                color,
                amplitude=amplitude,
                duration=duration,
                steps=steps,
            )
        )
        self._pulse_task.start()

    def pulse_stop(self):
        if (
            self._pulse_task is not None
            and threading.current_thread() is not self._pulse_task
        ):
            self._pulse_task.stop()
            self._pulse_task.join()
            self._pulse_task = None


def init():
    config = flask.current_app.config.get("ILLUMINATION", {})
    if isinstance(config, dict):
        config = config.get("neopixel")
    if not config or flask.current_app.testing:
        return
    logging.getLogger(__name__).info("Init")

    neo = NeopixelSpi(bus=config["bus"], device=config["device"], leds=config["leds"])

    for event in config["events"]:
        flask.current_app.events.register(
            event,
            lambda event=event: config["events"][event](neo),
        )


if __name__ == "__main__":
    neo = NeopixelSpi(bus=0, device=0, leds=12)
    neo.clear()
    neo.fill(235, 90, 7)
    try:
        while True:
            # neo.pulse((250, 170, 10), amplitude=0.8, duration=2)
            pass
    except KeyboardInterrupt:
        neo.clear()
        neo.update()
