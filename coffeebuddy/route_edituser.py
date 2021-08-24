import math

import flask
from flask import render_template, request, redirect, abort

from coffeebuddy.model import User, Drink


def handle_post(user):
    if user is None:
        # Add new user
        user = User(
            tag=bytes.fromhex(request.form['tag']),
            name=request.form['last_name'],
            prename=request.form['first_name'],
            option_oneswipe='oneswipe' in request.form,
        )
        flask.g.db.session.add(user)
        try:
            bill = float(request.form['initial_bill'].replace(',', '.'))
            for _ in range(math.ceil(bill / flask.g.app.config['PRICE'])):
                flask.g.db.session.add(Drink(user=user, price=flask.g.app.config['PRICE']))
        except ValueError:
            pass
        flask.g.db.session.commit()
    else:
        # Edit existing new user
        user.name = request.form['last_name']
        user.prename = request.form['first_name']
        user.option_oneswipe = 'oneswipe' in request.form
        flask.g.db.session.commit()
    return redirect('/')


def handle_get(user):
    data = {
        'tag': request.args['tag'],
    }
    return render_template('edituser.html', data=data, user=(user or User(name='', prename='')))


def init():
    @flask.g.app.route('/edituser.html', methods=['GET', 'POST'])
    def edit_user():
        tag = bytes.fromhex(request.args['tag']) if 'tag' in request.args else None
        user = User.query.filter(User.tag == tag).first()
        if request.method == 'POST':
            return handle_post(user)
        elif request.method == 'GET':
            return handle_get(user)
        return abort(404)
