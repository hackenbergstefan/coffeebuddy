from flask import Flask

app = Flask('coffeetag')


def create_app():
    # Import database
    import coffeetag.database
    app.db = coffeetag.database.init_db()

    # Import routes
    import coffeetag.routes
