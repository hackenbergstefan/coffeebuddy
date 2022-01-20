import socket

# Price per cup in €
PRICE = 0.30
# Amount in € to pay by one pay
PAY = 10
# Card type (PCSC, MRFC522, PIRC522)
CARD = 'PCSC'
# Database connection details
DB_BACKEND = 'sqlite'
if DB_BACKEND == 'postgres':
    SQLALCHEMY_DATABASE_URI = f'postgresql://{socket.gethostname()}@coffeebuddydb:5432/coffeebuddy'
    SQLALCHEMY_ENGINE_OPTIONS = {'connect_args': {'sslmode': 'verify-full'}}
elif DB_BACKEND == 'sqlite':
    SQLALCHEMY_DATABASE_URI = 'sqlite:///coffee.db'

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
