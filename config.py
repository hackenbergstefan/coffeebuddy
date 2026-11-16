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

# Charge only prices
PRICES_CHARGE_ONLY = {0.30, 0.55}

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

# Extension: Microsoft Teams (coffeebuddy.extensions.msteams)
# ---------------------------------------------
# Coffeebuddy sends messages on behalf of a dedicated Microsoft 365 account via
# Microsoft Graph. Setup:
# 1. Register an app in Microsoft Entra ID, create a client secret and add the
#    delegated Graph permissions User.Read.All, Chat.ReadWrite and Chat.Create
#    and ChannelMessage.Send, ChannelMessage.Read.All (payment notifications)
#    and Files.ReadWrite.All (MSTEAMS_DATABASE_BACKUP). Grant consent for them.
# 2. The Coffeebuddy account must not require MFA (username/password sign-in).
# Teams is disabled unless all of the following are set.
# Directory (tenant) id
MSTEAMS_TENANT_ID = None
# Application (client) id and client secret of the Entra ID app registration
MSTEAMS_CLIENT_ID = None
MSTEAMS_CLIENT_SECRET = None
# Credentials of the Coffeebuddy Microsoft 365 account
MSTEAMS_USERNAME = None
MSTEAMS_PASSWORD = None

# Email default domains (used to autofill user's name)
USER_EMAIL_DEFAULT_DOMAINS = ["@gmail.com", "@apple.com"]

# Teams reminder message (markdown), where "{oneliner}" is a randomized oneliner
REMINDER_MESSAGE = """Beep bop - greetings from the Coffeebuddy bot!

{oneliner}

NAME ROOM is looking forward to seeing you(r money)!
"""

# If not False, the Teams channel link ("Get link to channel") where to post
# database backup files and disabled accounts.
# The Coffeebuddy account must be a member of this channel.
MSTEAMS_DATABASE_BACKUP = False

# List of Teams channel links ("Get link to channel") which are notified when
# someone pays. The Coffeebuddy account must be a member of these channels.
PAYMENT_NOTIFICATION_CHANNELS = []

# Extension: Coffeemaker (coffeebuddy.extensions.coffeemaker)
# ---------------------------------------------
# Coffeemaker configuration
# Set `None` to disable
# Set `{"jura_ble": {"model": "EF658S_C", "address": "00:00:00"}}`
# for a JURA ble machine. Adjust model and address appropriately.
# Set `{"jura_ble_mock": {"model": "EF658S_C", "brew_time": 10}}` to enable a jura mock
COFFEEMAKER = {"jura_ble_mock": {"model": "EF658S_C", "brew_time": 10}}
