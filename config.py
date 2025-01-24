import socket

# Global settings
# ===============

# Whether to prefill the database
PREFILLED = True

# Database connection details
DB_BACKEND = "sqlite"
if DB_BACKEND == "postgres":
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{socket.gethostname()}@coffeebuddydb:5432/coffeebuddy"
    )
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"sslmode": "verify-full"}}
elif DB_BACKEND == "sqlite":
    SQLALCHEMY_DATABASE_URI = "sqlite:///coffee.db"

# Price per cup in €
PRICE = 0.30

# Guest account enabled
GUEST = False

# Enable https
SSL = False

# Localization
TIMEZONE = "Europe/Berlin"
COUNTRY = {"country": "DE", "subdiv": "BY"}

# Secret key for session cookies
SECRET_KEY = "coffeebuddy"

# Password for admin access
ADMIN_PASSWORD = "coffeebuddy"


# Extensions
# ==========

# Extension: Card (coffeebuddy.extensions.card)
# ---------------------------------------------
# Card type (PCSC, MRFC522, PIRC522)
CARD = "PCSC"

# Extension: Illumination
# (coffeebuddy.extensions.illumination, coffeebuddy.extensions.illumination_neopixel)
# ---------------------------------------------
# If using coffeebuddy.extensions.illumination:
# `{"pins": (1, 2, 3), "color_motion_detected": "rose", "color_X": ...}`.
# See ./coffeebuddy/illumination.py for details
# If using coffeebuddy.extensions.illumination_neopixel. E.g.
# ```py
# ILLUMINATION = {
#     "neopixel": {
#         "bus": 0,
#         "device": 0,
#         "leds": 12,
#         "events": {
#             "route:/": lambda neo: neo.fill(20, 10, 10),
#             re.compile("route:/.+"): lambda neo: neo.fill(235, 90, 7),
#             "coffeemaker:brew:stop": lambda neo: neo.fill(235, 90, 7),
#             "coffeemaker:brew:start": lambda neo: neo.pulse(
#                 (250, 170, 10),
#                 amplitude=0.8,
#                 duration=2,
#             ),
#         },
#     }
# }
# ```
# See ./coffeebuddy/illumination_neopixel.py for details
ILLUMINATION = None

# Extension: PIR (coffeebuddy.extensions.pir)
# ---------------------------------------------
# PIR motion detection (None if not used, BCM pin number otherwise)
PIR = None

# Extension: Display on-off (coffeebuddy.extensions.display_on_off)
# ---------------------------------------------
# Switch display on and off by motion detection
DISPLAY_ON_OFF = False

# Extension: WebEx (coffeebuddy.extensions.webex)
# ---------------------------------------------
# Webex Access Token
WEBEX_ACCESS_TOKEN = None

# Email default domains (used to autofill user's name)
USER_EMAIL_DEFAULT_DOMAINS = ["@gmail.com", "@apple.com"]

# Webex reminder message, where"{oneliner} is a randomized oneliner by coffeebuddy
REMINDER_MESSAGE = """Beep bop - greetings from the Coffeebuddy bot!

{oneliner}

NAME ROOM is looking forward to seeing you(r money)!
"""

# If not False, the webex roomid where to post database backup files
WEBEX_DATABASE_BACKUP = False

# List of peoples' emails who are notified when someone pays
PAYMENT_NOTIFICATION_EMAILS = []

# Extension: Coffeemaker (coffeebuddy.extensions.coffeemaker)
# ---------------------------------------------
# Coffeemaker configuration
# Set `None` to disable
# Set `{"mock": 10.0}` to enable mock with 10 seconds brew time
# Set `{"jura_ble": {"model": "xzy", "address": "00:00:00"}}`
COFFEEMAKER = {"jura_ble": {"model": "xzy", "address": "00:00:00"}}
