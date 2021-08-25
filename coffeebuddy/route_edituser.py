import math

import flask

from coffeebuddy.model import User, Drink


def handle_post(user):
    if user is None:
        # Add new user
        user = User(
            tag=bytes.fromhex(flask.request.form['tag']),
            name=flask.request.form['last_name'],
            prename=flask.request.form['first_name'],
            option_oneswipe='oneswipe' in flask.request.form,
        )
        flask.current_app.db.session.add(user)
        try:
            bill = float(flask.request.form['initial_bill'].replace(',', '.'))
            for _ in range(math.ceil(bill / flask.current_app.config['PRICE'])):
                flask.current_app.db.session.add(Drink(user=user, price=flask.current_app.config['PRICE']))
        except ValueError:
            pass
        flask.current_app.db.session.commit()
    else:
        # Edit existing new user
        user.name = flask.request.form['last_name']
        user.prename = flask.request.form['first_name']
        user.option_oneswipe = 'oneswipe' in flask.request.form
        flask.current_app.db.session.commit()
    return flask.redirect('/')


def handle_get(user):
    data = {
        'tag': flask.request.args['tag'],
    }
    return flask.render_template('edituser.html', data=data, user=(user or User(name='', prename='')))


def init():
    @flask.current_app.route('/edituser.html', methods=['GET', 'POST'])
    def edit_user():
        tag = bytes.fromhex(flask.request.args['tag']) if 'tag' in flask.request.args else None
        user = User.query.filter(User.tag == tag).first()
        if flask.request.method == 'POST':
            return handle_post(user)
        elif flask.request.method == 'GET':
            return handle_get(user)
        return flask.abort(404)
