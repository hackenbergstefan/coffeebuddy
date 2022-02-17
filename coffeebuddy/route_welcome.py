import datetime
import socket
import subprocess

import flask

from coffeebuddy.model import Drink


def init():
    @flask.current_app.route('/')
    def welcome():
        data = [
            (amount, date if isinstance(date, str) else date.strftime('%Y-%m-%d'))
            for amount, date in Drink.drinks_vs_days(datetime.timedelta(weeks=12))
        ]
        return flask.render_template(
            'welcome.html',
            dataset=data,
            hostname=socket.gethostname(),
            githash=subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip(),
        )
