from flask import url_for, render_template, request, abort
from coffeetag.model import User, Drink, Pay


def init_routes(app):
    @app.route('/coffee.html', methods=['GET', 'POST'])
    def hello():
        user = User.query.filter(User.tag == request.args['tag'].encode()).first()
        if user is None:
            return abort(404)
        if request.method == 'POST':
            if 'coffee' in request.form:
                app.db.session.add(Drink(user=user, price=app.config['PRICE']))
                app.db.session.commit()
            elif 'pay' in request.form:
                app.db.session.add(Pay(user=user, amount=request.form['pay']))
                app.db.session.commit()
        return render_template('coffee.html', user=user)

    @app.route('/')
    def welcome():
        return render_template('welcome.html')
