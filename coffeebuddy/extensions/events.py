import logging
import re

import flask

"""
This module provides a simple event manager to register and fire events.
"""


class EventManager:
    def __init__(self):
        self.events = {}
        self.locked = set()

    def fire(self, eventname, **kwargs):
        logging.getLogger(__name__).info(f"Fire {eventname}({kwargs})")
        if eventname in self.events:
            for func in self.events[eventname]:
                func(**kwargs)
        for ev, funcs in self.events.items():
            if isinstance(ev, re.Pattern) and ev.match(eventname):
                for func in funcs:
                    func(**kwargs)

    def register(self, eventname, func):
        logging.getLogger(__name__).info(f"Register {eventname} {func}")
        if eventname in self.events:
            self.events[eventname].append(func)
        else:
            self.events[eventname] = [func]


def init():
    flask.current_app.events = EventManager()
    flask.current_app.socketio.on_event(
        "route",
        lambda route: flask.current_app.events.fire(
            f"route:{route.replace('.html','')}"
        ),
    )
