import flask
from flask import request, render_template, redirect

from coffeebuddy.model import User


class Color:
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    def __str__(self):
        return f"rgb({self.r}, {self.g}, {self.b})"

    def brighter(self, factor):
        r = self.r + (255 - self.r) * factor
        g = self.g + (255 - self.g) * factor
        b = self.b + (255 - self.b) * factor
        return Color(r, g, b)


def init():
    @flask.g.app.route('/stats.html', methods=['GET', 'POST'])
    def chart():
        user = User.query.filter(User.tag == bytes.fromhex(request.args['tag'])).first()
        if user is None:
            return render_template('cardnotfound.html', uuid=request.args['tag'])

        if request.method == 'POST':
            if 'coffee' in request.form:
                return redirect(f'coffee.html?tag={request.args["tag"]}')
            elif 'logout' in request.form:
                return redirect('/')

        berry = Color(171, 55, 122)

        x = list(user.drink_days)
        n = user.max_drinks_per_day
        datasets = [
            {
                'x': x,
                'y': [f'1970-01-01T{user.nth_drink(date, i).timestamp.time().isoformat()}' for date in x],
                'fill': 'tozeroy',
                'name': f'{i}. Coffee',
                'mode': 'markers',
                'fillcolor': str(berry.brighter(1 - i / n)),
                'line': {
                    'color': str(berry),
                }
            } for i in range(n, 0, -1)
        ]

        return render_template('stats.html', user=user, datasets=datasets)
