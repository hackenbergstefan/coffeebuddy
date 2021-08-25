import flask

from coffeebuddy.model import User, Drink


def init():
    @flask.current_app.route('/oneswipe.html', methods=['POST'])
    def oneswipe():
        user = User.query.filter(User.tag == bytes.fromhex(flask.request.args['tag'])).first()
        if 'coffee' in flask.request.form:
            flask.current_app.db.session.add(Drink(user=user, price=flask.current_app.config['PRICE']))
            flask.current_app.db.session.commit()
        return ''
