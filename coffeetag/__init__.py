from flask import Flask

app = Flask('coffeetag')


@app.context_processor
def inject_globals():
    return {
        'len': len
    }


@app.teardown_appcontext
def shutdown_session(exception=None):
    app.db.remove()


def create_app():
    # Import database
    import coffeetag.database
    app.db = coffeetag.database.init_db()

    # Import routes
    import coffeetag.routes
