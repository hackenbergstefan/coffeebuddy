import importlib
from pathlib import Path

import coffeebuddy.extensions.events


def init():
    """
    Import all extensions from the extensions directory.
    """
    # Preinit events
    coffeebuddy.extensions.events.init()

    for ext in Path(__file__).parent.glob("*.py"):
        if ext.name.startswith("__") or ext.name == "events.py":
            continue
        module = importlib.import_module(f"coffeebuddy.extensions.{ext.stem}")
        module.init()
