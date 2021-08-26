import flask


def init():
    if flask.current_app.testing:
        return

    if flask.current_app.config['ILLUMINATION'] is True:
        import coffeebuddy.illumination

        coffeebuddy.illumination.init()
