import flask

from coffeebuddy.model import User


def init():
    @flask.current_app.route('/selectuser.html')
    def selectuser():
        return flask.render_template(
            'selectuser.html',
            User=User,
        )
