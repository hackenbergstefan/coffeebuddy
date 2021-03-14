from flask import url_for, render_template, request, abort, g
from coffeetag.model import User, Drink


def init_routes(app):
    @app.route('/coffee.html', methods=['GET', 'POST'])
    def hello():
        user = User.query.filter(User.tag == request.args['tag'].encode()).first()
        if user is None:
            return abort(404)
        if request.method == 'POST' and 'coffee' in request.form:
            g.db.session.add(Drink(user=user))
            g.db.session.commit()
        return render_template('coffee.html', user=user)
