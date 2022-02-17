import flask


def init():
    @flask.current_app.context_processor
    def inject_globals():
        return {
            'len': len,
            'round': round,
            'max': max,
            'min': min,
            'hexstr': lambda data: ' '.join(f'{x:02x}' for x in data) if data else '',
        }

    @flask.current_app.after_request
    def after_request(response):
        if flask.request.endpoint:
            if flask.request.endpoint == 'welcome':
                flask.current_app.events.fire('route_welcome')
            elif flask.request.endpoint != 'static':
                flask.current_app.events.fire('route_notwelcome')
        return response

    import coffeebuddy.route_coffee

    coffeebuddy.route_coffee.init()

    import coffeebuddy.route_chart

    coffeebuddy.route_chart.init()

    import coffeebuddy.route_edituser

    coffeebuddy.route_edituser.init()

    import coffeebuddy.route_oneswipe

    coffeebuddy.route_oneswipe.init()

    import coffeebuddy.route_tables

    coffeebuddy.route_tables.init()

    import coffeebuddy.route_welcome

    coffeebuddy.route_welcome.init()

    import coffeebuddy.route_selectuser

    coffeebuddy.route_selectuser.init()
