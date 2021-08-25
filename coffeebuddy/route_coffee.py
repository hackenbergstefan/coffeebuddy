import flask

from coffeebuddy.model import Drink, User, Pay


def init():
    @flask.g.app.route('/coffee.html', methods=['GET', 'POST'])
    def coffee():
        flask.g.events.fire('route_coffee')
        user = User.query.filter(User.tag == bytes.fromhex(flask.request.args['tag'])).first()
        if user is None:
            return flask.render_template('cardnotfound.html', uuid=flask.request.args['tag'])
        if flask.request.method == 'GET' and user.option_oneswipe:
            return flask.render_template('oneswipe.html', user=user)
        if flask.request.method == 'POST':
            if 'coffee' in flask.request.form:
                flask.g.db.session.add(Drink(user=user, price=flask.g.app.config['PRICE']))
                flask.g.db.session.commit()
            elif 'pay' in flask.request.form:
                flask.g.db.session.add(Pay(user=user, amount=flask.request.form['pay']))
                flask.g.db.session.commit()
            elif 'undopay' in flask.request.form:
                # TODO: Really deleting pay? Introduce property 'undone' on Pay?
                if len(user.pays) > 0:
                    flask.g.db.session.delete(user.pays[-1])
                    flask.g.db.session.commit()
            elif 'logout' in flask.request.form:
                return flask.redirect('/')
            elif 'edituser' in flask.request.form:
                return flask.redirect(f'edituser.html?tag={flask.request.args["tag"]}')
            elif 'stats' in flask.request.form:
                return flask.redirect(f'stats.html?tag={flask.request.args["tag"]}')
            elif 'capture' in flask.request.form:
                if 'notimeout' in flask.request.args:
                    flask.g.events.fire('route_coffee_capture', user)
                return flask.redirect(f'{flask.request.url}&notimeout')

        return flask.render_template(
            'coffee.html',
            user=user,
            referer=flask.request.form if flask.request.method == 'POST' else [],
        )
