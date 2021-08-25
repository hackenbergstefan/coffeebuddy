import flask

def init():
    if flask.g.app.testing:
        return

    if flask.g.app.config['PIR'] is True:
        import coffeebuddy.pir
        coffeebuddy.pir.init()

    if flask.g.app.config['ILLUMINATION'] is True:
        import coffeebuddy.illumination
        coffeebuddy.illumination.init()
