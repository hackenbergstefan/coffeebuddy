import datetime
from sqlalchemy import text

from coffeebuddy import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.LargeBinary, nullable=False, unique=True)
    name = db.Column(db.String(50), nullable=False)
    prename = db.Column(db.String(50), nullable=False)
    option_oneswipe = db.Column(db.Boolean)

    @property
    def coffees_today(self):
        return Drink.query.filter(
            self.id == Drink.userid,
            db.func.Date(Drink.timestamp) == datetime.date.today()
        ).all()

    @property
    def unpayed(self):
        # TODO: Fast enough?
        return sum(c.price for c in self.coffees) - sum(p.amount for p in self.pays)

    def drinks(self, date=None):
        drinks = Drink.query.filter(self.id == Drink.userid)
        if date is not None:
            drinks = drinks.filter(db.func.Date(Drink.timestamp) == date)
        drinks = drinks.order_by(Drink.timestamp)
        return drinks

    def nth_drink(self, date, n):
        return self.drinks(date).limit(n)[-1]

    @property
    def drinks_per_day(self):
        return (
            db.session.query(db.func.Date(Drink.timestamp), db.func.count(db.func.Date(Drink.timestamp)))
            .filter(self.id == Drink.userid)
            .group_by(db.func.Date(Drink.timestamp))
        )

    @property
    def max_drinks_per_day(self):
        _date, drinks = self.drinks_per_day.order_by(text("count_1"))[-1]
        return drinks

    @property
    def drink_days(self):
        return (
            tup[0] for tup in
            db.session.query(db.func.Date(Drink.timestamp))
            .filter(self.id == Drink.userid)
            .distinct()
            .order_by(Drink.timestamp)
        )

    def __repr__(self):
        return f'<User tag={self.tag} name={self.name} prename={self.prename}>'


class Drink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    price = db.Column(db.Integer, nullable=False)
    userid = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('coffees', lazy=True))

    def __init__(self, *args, **kwargs):
        if 'timestamp' not in kwargs:
            kwargs['timestamp'] = datetime.datetime.now()
        super().__init__(*args, **kwargs)

    def by_date(date):
        return Drink.query.filter(db.func.Date(Drink.timestamp) == date)

    @staticmethod
    def drinks_vs_days(timedelta):
        return (
            db.session.query(
                db.func.count(db.func.Date(Drink.timestamp)),
                db.func.Date(Drink.timestamp),
            )
            .filter(Drink.timestamp > datetime.datetime.now() - timedelta)
            .group_by(db.func.Date(Drink.timestamp))
            .all()
        )


class Pay(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    userid = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('pays', lazy=True))
    amount = db.Column(db.Integer, nullable=False)

    def __init__(self, *args, **kwargs):
        if 'timestamp' not in kwargs:
            kwargs['timestamp'] = datetime.datetime.now()
        super().__init__(*args, **kwargs)
