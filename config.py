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

# Extension: Illumination (coffeebuddy.extensions.illumination)
# ---------------------------------------------
# If set: `{"pins": (1, 2, 3), "color_motion_detected": "rose", "color_X": ...}`.
# See ./coffeebuddy/illumination.py for details
ILLUMINATION = False

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

# Set True if real coffeemaker is attached
COFFEEMAKER = False

# Number of seconds a coffee takes to be brewed.
# Set to False to disable mock.
COFFEEMAKER_MOCK_BREW_TIME = 10.0
