import datetime
import math

from flask import render_template, request, redirect
from flask.ctx import after_this_request

from coffeebuddy.model import User, Drink, Pay, db
from coffeebuddy.card import PCSCCard, MRFC522Card, PIRC522Card
from coffeebuddy import facerecognition, facerecognition_threaded


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

def init_routes(app, socketio):
    @app.after_request
    def after_request(response):
        if app.config['FACERECOGNITION'] is True and request.endpoint:
            if request.endpoint == 'welcome':
                print(request.base_url, request.path, request.values, request.args, request.endpoint)
                facerecognition_threaded.resume()
            elif request.endpoint != 'static':
                print(request.base_url, request.path, request.values, request.args, request.endpoint)
                facerecognition_threaded.pause()
        return response

    @app.route('/coffee.html', methods=['GET', 'POST'])
    def coffee():
        user = User.query.filter(User.tag == bytes.fromhex(request.args['tag'])).first()
        if user is None:
            return render_template('cardnotfound.html', uuid=request.args['tag'])
        if request.method == 'GET' and user.option_oneswipe:
            return render_template('oneswipe.html', user=user)
        if request.method == 'POST':
            if 'coffee' in request.form:
                app.db.session.add(Drink(user=user, price=app.config['PRICE']))
                app.db.session.commit()
            elif 'pay' in request.form:
                app.db.session.add(Pay(user=user, amount=request.form['pay']))
                app.db.session.commit()
            elif 'undopay' in request.form:
                # TODO: Really deleting pay? Introduce property 'undone' on Pay?
                if len(user.pays) > 0:
                    app.db.session.delete(user.pays[-1])
                    app.db.session.commit()
            elif 'logout' in request.form:
                return redirect('/')
            elif 'edituser' in request.form:
                return redirect(f'edituser.html?tag={request.args["tag"]}')
            elif 'stats' in request.form:
                return redirect(f'stats.html?tag={request.args["tag"]}')
            elif 'capture' in request.form:
                if 'notimeout' in request.args:
                    if app.config['FACERECOGNITION'] is True:
                        facerecognition_threaded.pause()
                        facerecognition.FaceCapturer(user.tag, user.name, user.prename).capture()
                return redirect(f'{request.url}&notimeout')

        return render_template(
            'coffee.html',
            user=user,
            referer=request.form if request.method == 'POST' else [],
        )

    @app.route('/stats.html', methods=['GET', 'POST'])
    def chart():
        user = User.query.filter(User.tag == bytes.fromhex(request.args['tag'])).first()
        if user is None:
            return render_template('cardnotfound.html', uuid=request.args['tag'])

        if request.method == 'POST':
            if 'coffee' in request.form:
                return redirect(f'coffee.html?tag={request.args["tag"]}')
            elif 'logout' in request.form:
                return redirect('/')

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
                }
            } for i in range(n, 0, -1)
        ]

        return render_template('stats.html', user=user, datasets=datasets)

    @app.route('/')
    def welcome():
        return render_template(
            'welcome.html',
            dataset=Drink.drinks_vs_days(datetime.timedelta(weeks=12))
        )

    @app.route('/edituser.html', methods=['GET', 'POST'])
    def edit_user():
        data = dict()
        tag = bytes.fromhex(request.args['tag']) if 'tag' in request.args else None
        user = User.query.filter(User.tag == tag).first()
        if request.method == 'POST':
            # TODO: Errorhandling
            if user is None:
                # Add new user
                user = User(
                    tag=bytes.fromhex(request.form['tag']),
                    name=request.form['last_name'],
                    prename=request.form['first_name'],
                    option_oneswipe='oneswipe' in request.form,
                )
                app.db.session.add(user)
                try:
                    bill = float(request.form['initial_bill'].replace(',', '.'))
                    for _ in range(math.ceil(bill / app.config['PRICE'])):
                        app.db.session.add(Drink(user=user, price=app.config['PRICE']))
                except ValueError:
                    pass
                app.db.session.commit()
            else:
                # Edit existing new user
                user.name = request.form['last_name']
                user.prename = request.form['first_name']
                user.option_oneswipe = 'oneswipe' in request.form
                app.db.session.commit()
            return redirect('/')
        elif request.method == 'GET':
            data = {
                'tag': request.args['tag'],
            }
        return render_template('edituser.html', data=data, user=(user or User(name='', prename='')))

    @app.route('/oneswipe.html', methods=['POST'])
    def oneswipe():
        user = User.query.filter(User.tag == bytes.fromhex(request.args['tag'])).first()
        if 'coffee' in request.form:
            app.db.session.add(Drink(user=user, price=app.config['PRICE']))
            app.db.session.commit()

    @app.route('/tables.html')
    def tables():
        return render_template(
            'tables.html',
            bills=[
                (user.name, user.prename, user.tag.hex(), round(user.unpayed, 2))
                for user in User.query.all()
            ],
            drinks=[
                (str(drink.timestamp), drink.user.name, drink.user.prename, drink.price)
                for drink in
                Drink.query.filter(db.func.Date(Drink.timestamp) >= datetime.date.today() - datetime.timedelta(days=30))
                if drink.user
            ]
        )

    if not app.testing:
        if app.config['CARD'] == 'MRFC522':
            MRFC522Card(socketio=socketio).start()
        elif app.config['CARD'] == 'PCSC':
            PCSCCard(socketio=socketio).start()
        elif app.config['CARD'] == 'PIRC522':
            PIRC522Card(socketio=socketio).start()

        if app.config['FACERECOGNITION'] is True:
            facerecognition_threaded.start(socketio)
