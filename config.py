import socket

# Price per cup in €
PRICE = 0.30
# Amount in € to pay by one pay
PAY = 10
# Card type (PCSC, MRFC522, PIRC522)
CARD = "PCSC"
# Database connection details
DB_BACKEND = "sqlite"
if DB_BACKEND == "postgres":
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{socket.gethostname()}@coffeebuddydb:5432/coffeebuddy"
    )
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"sslmode": "verify-full"}}
elif DB_BACKEND == "sqlite":
    SQLALCHEMY_DATABASE_URI = "sqlite:///coffee.db"

# Enable camera
CAMERA = False

# Enable Facerecognition
FACERECOGNITION = False

# Illumination
ILLUMINATION = False

# PIR motion detection (None if not used, BCM pin number otherwise)
PIR = None

# Switch display on and off by motion detection
MOTION_DISPLAY_CONTROL = False

# Guest account enabled
GUEST = False

# Disable automatic timeout from coffee.html
NOTIMEOUT = False

# Enable https
SSL = False

# Webex Access Token
WEBEX_ACCESS_TOKEN = None

# Email default domains
USER_EMAIL_DEFAULT_DOMAINS = ["@gmail.com", "@apple.com"]

# Webex reminder message, where"{oneliner} is a randomized oneliner by coffeebuddy
REMINDER_MESSAGE = """Beep bop - greetings from the Coffeebuddy bot!

{oneliner}

NAME ROOM is looking forward to seeing you(r money)!
"""

# List of peoples' emails who are notified when someone pays
PAYMENT_NOTIFICATION_EMAILS = []

# Localization
TIMEZONE = "Europe/Berlin"
COUNTRY = {"country": "DE", "subdiv": "BY"}

# Secret key for session cookies
SECRET_KEY = "coffeebuddy"

# Password for admin access
ADMIN_PASSWORD = "coffeebuddy"
