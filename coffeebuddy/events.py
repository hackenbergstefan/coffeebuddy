import logging


class EventManager:
    def __init__(self):
        self.events = {}
        self.locked = set()

    def fire(self, eventname, **kwargs):
        logging.getLogger(__name__).info(f'Fire {eventname}({kwargs})')
        if eventname in self.events:
            for func in self.events[eventname]:
                func(**kwargs)

    def register(self, eventname, func):
        logging.getLogger(__name__).info(f'Register {eventname} {func}')
        if eventname in self.events:
            self.events[eventname].append(func)
        else:
            self.events[eventname] = [func]

    def fire_once(self, eventname, **kwargs):
        """Fire eventname once until fire_reset is called."""
        if eventname in self.locked:
            return

        self.locked.add(eventname)
        self.fire(eventname, **kwargs)

    def fire_reset(self, eventname):
        if eventname in self.locked:
            self.locked.remove(eventname)

    def block(self, eventname):
        if eventname in self.locked:
            return

        self.locked.add(eventname)
