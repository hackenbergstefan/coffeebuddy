from pathlib import Path

import qrcode
from qrcode.image.svg import SvgPathImage

from coffeebuddy import __version__

"""
This extension just generates a qr code to the help pages.
"""

HELP_URL = f"github.com/hackenbergstefan/coffeebuddy/blob/v{__version__}/doc/HELP.md"


def init():
    qr = qrcode.QRCode(border=0, box_size=10, image_factory=SvgPathImage)
    qr.add_data(HELP_URL)
    qr.make(fit=True)
    (Path(__file__).parent.parent / "static" / "qrhelp.svg").write_bytes(
        qr.make_image(attrib={"class": "qrhelp"}).to_string()
    )
