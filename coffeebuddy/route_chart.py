import flask

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
    @flask.current_app.route('/stats.html', methods=['GET', 'POST'])
    def chart():
        user = User.by_tag(bytes.fromhex(flask.request.args['tag']))
        if user is None:
            return flask.render_template('cardnotfound.html', uuid=flask.request.args['tag'])

        if flask.request.method == 'POST':
            if 'coffee' in flask.request.form:
                return flask.redirect(f'coffee.html?tag={flask.request.args["tag"]}')
            elif 'logout' in flask.request.form:
                return flask.redirect('/')

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
                },
            }
            for i in range(n, 0, -1)
        ]

        return flask.render_template('stats.html', user=user, datasets=datasets)
