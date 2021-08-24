import flask
from flask import request, abort

from coffeebuddy.model import User, Drink


def init():
    @flask.g.app.route('/oneswipe.html', methods=['POST'])
    def oneswipe():
        user = User.query.filter(User.tag == bytes.fromhex(request.args['tag'])).first()
        if 'coffee' in request.form:
            flask.g.db.session.add(Drink(user=user, price=flask.g.app.config['PRICE']))
            flask.g.db.session.commit()
        return abort(404)
