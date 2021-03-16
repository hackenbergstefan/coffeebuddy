from flask import url_for, render_template, request, abort, redirect
import flask_socketio
from coffeetag.model import User, Drink, Pay
from coffeetag.card import Card


def init_routes(app, socketio):
    @app.route('/coffee.html', methods=['GET', 'POST'])
    def hello():
        user = User.query.filter(User.tag == bytes.fromhex(request.args['tag'])).first()
        if user is None:
            return render_template('cardnotfound.html', uuid=request.args['tag'])
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

    @app.route('/adduser.html', methods=['GET', 'POST'])
    def add_user():
        data = dict()
        if request.method == 'POST':
            # TODO: Errorhandling
            app.db.session.add(User(
                tag=bytes.fromhex(request.form['tag']),
                name=request.form['last_name'],
                prename=request.form['first_name'],
            ))
            app.db.session.commit()
            return redirect('/')
        elif request.method == 'GET':
            data = {
                'tag': request.args.get('tag'),
            }
        return render_template('adduser.html', data=data)

    if not app.testing:
        Card(socketio=socketio).start()
