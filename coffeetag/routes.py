import threading
from flask import url_for, render_template, request, abort
import flask_socketio
from coffeetag.model import User, Drink, Pay

poll_thread = None


def poll_card():
    import time
    from coffeetag import socketio
    time.sleep(5)
    socketio.emit('card_connected', data={'tag': '1'})


def init_routes(app, socketio):
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
        global poll_thread
        if not app.testing:
            poll_thread = threading.Thread(target=poll_card)
            poll_thread.start()
        return render_template('welcome.html')

    @app.route('/adduser.html', methods=['GET', 'POST'])
    def add_user():
        if request.method == 'POST':
            # TODO: Errorhandling
            app.db.session.add(User(
                tag=bytes.fromhex(request.form['tag']),
                name=request.form['last_name'],
                prename=request.form['first_name'],
            ))
            app.db.session.commit()
        return render_template('adduser.html')
