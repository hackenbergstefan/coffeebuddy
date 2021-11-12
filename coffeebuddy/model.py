import datetime

import flask
from sqlalchemy import text


class User(flask.current_app.db.Model):
    id = flask.current_app.db.Column(flask.current_app.db.Integer, primary_key=True)
    tag = flask.current_app.db.Column(flask.current_app.db.LargeBinary, nullable=False, unique=True)
    name = flask.current_app.db.Column(flask.current_app.db.String(50), nullable=False)
    prename = flask.current_app.db.Column(flask.current_app.db.String(50), nullable=False)
    option_oneswipe = flask.current_app.db.Column(flask.current_app.db.Boolean)

    @property
    def coffees_today(self):
        return Drink.query.filter(
            self.id == Drink.userid, flask.current_app.db.func.Date(Drink.timestamp) == datetime.date.today()
        ).all()

    @property
    def unpayed(self):
        # TODO: Fast enough?
        return sum(c.price for c in self.coffees) - sum(p.amount for p in self.pays)

    def drinks(self, date=None):
        drinks = Drink.query.filter(self.id == Drink.userid)
        if date is not None:
            drinks = drinks.filter(flask.current_app.db.func.Date(Drink.timestamp) == date)
        drinks = drinks.order_by(Drink.timestamp)
        return drinks

    def nth_drink(self, date, n):
        return self.drinks(date).limit(n)[-1]

    @property
    def drinks_per_day(self):
        return (
            flask.current_app.db.session.query(
                flask.current_app.db.func.Date(Drink.timestamp),
                flask.current_app.db.func.count(flask.current_app.db.func.Date(Drink.timestamp)),
            )
            .filter(self.id == Drink.userid)
            .group_by(flask.current_app.db.func.Date(Drink.timestamp))
        )

    @property
    def max_drinks_per_day(self):
        try:
            _date, drinks = self.drinks_per_day.order_by(text("count_1"))[-1]
            return drinks
        except IndexError:
            return 0

    @property
    def drink_days(self):
        return (
            tup[0]
            for tup in flask.current_app.db.session.query(flask.current_app.db.func.Date(Drink.timestamp))
            .filter(self.id == Drink.userid)
            .distinct()
            .order_by(Drink.timestamp)
        )

    def __repr__(self):
        return f'<User tag={self.tag} name={self.name} prename={self.prename}>'


class Drink(flask.current_app.db.Model):
    id = flask.current_app.db.Column(flask.current_app.db.Integer, primary_key=True)
    timestamp = flask.current_app.db.Column(flask.current_app.db.DateTime)
    price = flask.current_app.db.Column(flask.current_app.db.Float, nullable=False)
    userid = flask.current_app.db.Column(
        flask.current_app.db.Integer, flask.current_app.db.ForeignKey('user.id'), nullable=False
    )
    user = flask.current_app.db.relationship('User', cascade='all,delete', backref=flask.current_app.db.backref('coffees', lazy=True))

    def __init__(self, *args, **kwargs):
        if 'timestamp' not in kwargs:
            kwargs['timestamp'] = datetime.datetime.now()
        super().__init__(*args, **kwargs)

    def by_date(date):
        return Drink.query.filter(flask.current_app.db.func.Date(Drink.timestamp) == date)

    @staticmethod
    def drinks_vs_days(timedelta):
        return (
            flask.current_app.db.session.query(
                flask.current_app.db.func.count(flask.current_app.db.func.Date(Drink.timestamp)),
                flask.current_app.db.func.Date(Drink.timestamp),
            )
            .filter(Drink.timestamp > datetime.datetime.now() - timedelta)
            .group_by(flask.current_app.db.func.Date(Drink.timestamp))
            .all()
        )


class Pay(flask.current_app.db.Model):
    id = flask.current_app.db.Column(flask.current_app.db.Integer, primary_key=True)
    timestamp = flask.current_app.db.Column(flask.current_app.db.DateTime, nullable=False)
    userid = flask.current_app.db.Column(
        flask.current_app.db.Integer, flask.current_app.db.ForeignKey('user.id'), nullable=False
    )
    user = flask.current_app.db.relationship('User', cascade='all,delete', backref=flask.current_app.db.backref('pays', lazy=True))
    amount = flask.current_app.db.Column(flask.current_app.db.Float, nullable=False)

    def __init__(self, *args, **kwargs):
        if 'timestamp' not in kwargs:
            kwargs['timestamp'] = datetime.datetime.now()
        super().__init__(*args, **kwargs)
