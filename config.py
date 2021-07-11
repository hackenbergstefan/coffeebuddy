import socket

 # Price per cup in €
PRICE = 0.30
 # Amount in € to pay by one pay
PAY = 10
# Card type
CARD = 'PCSC'
# Database connection details
DB_BACKEND = 'postgres'
DB_HOST = 'coffeebuddydb'
DB_PORT = 5432
DB_USER = socket.gethostname()