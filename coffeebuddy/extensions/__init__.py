import importlib
from pathlib import Path

import coffeebuddy.extensions.events
import coffeebuddy.extensions.prefilled


def init():
    """
    Import all extensions from the extensions directory.
    """
    # Preinit extensions necessary for others
    coffeebuddy.extensions.events.init()
    coffeebuddy.extensions.prefilled.init()

    for ext in Path(__file__).parent.glob("*.py"):
        if ext.name.startswith("__") or ext.name in ("events.py", "prefilled.py"):
            continue
        module = importlib.import_module(f"coffeebuddy.extensions.{ext.stem}")
        module.init()
