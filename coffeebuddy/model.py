import datetime
import socket

import flask
import sqlalchemy
from sqlalchemy import text


class Serializer:
    @staticmethod
    def escape(obj):
        if isinstance(obj, bytes):
            return obj.hex()
        return obj

    def serialize(self):
        return {
            c: self.escape(getattr(self, c))
            for c in sqlalchemy.inspection.inspect(self).attrs.keys()
            if c not in sqlalchemy.inspect(self.__class__).relationships.keys()
        }


class User(flask.current_app.db.Model, Serializer):
    id = flask.current_app.db.Column(flask.current_app.db.Integer, primary_key=True)
    tag = flask.current_app.db.Column(flask.current_app.db.LargeBinary, nullable=False, unique=True)
    tag2 = flask.current_app.db.Column(flask.current_app.db.LargeBinary, unique=True, default=None)
    name = flask.current_app.db.Column(flask.current_app.db.String(50), nullable=False)
    prename = flask.current_app.db.Column(flask.current_app.db.String(50), nullable=False)
    email = flask.current_app.db.Column(flask.current_app.db.String(50))
    option_oneswipe = flask.current_app.db.Column(flask.current_app.db.Boolean, default=False)
    pays = flask.current_app.db.relationship("Pay", backref="user", cascade="all, delete")
    drinks = flask.current_app.db.relationship("Drink", backref="user", cascade="all, delete")

    @staticmethod
    def by_tag(tag):
        return User.query.filter((User.tag == tag) | ((User.tag2 != None) & (User.tag2 == tag))).first()  # noqa: E711

    @property
    def drinks_today(self):
        return (
            Drink.query.filter(Drink.user == self)
            .filter(flask.current_app.db.func.Date(Drink.timestamp) == datetime.date.today())
            .all()
        )

    @property
    def unpayed(self):
        # TODO: Fast enough?
        return sum(c.price for c in self.drinks) - sum(p.amount for p in self.pays)

    def nth_drink(self, date, n):
        return (
            Drink.query.filter(Drink.user == self)
            .filter(flask.current_app.db.func.Date(Drink.timestamp) == date)
            .limit(n)[-1]
        )

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
        return f"<User tag={self.tag} tag2={self.tag2} name={self.name} prename={self.prename} email={self.email}>"


class Drink(flask.current_app.db.Model):
    id = flask.current_app.db.Column(flask.current_app.db.Integer, primary_key=True)
    timestamp = flask.current_app.db.Column(flask.current_app.db.DateTime)
    price = flask.current_app.db.Column(flask.current_app.db.Float, nullable=False)
    userid = flask.current_app.db.Column(
        flask.current_app.db.Integer, flask.current_app.db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    host = flask.current_app.db.Column(flask.current_app.db.String(50))

    def __init__(self, *args, **kwargs):
        if "timestamp" not in kwargs:
            kwargs["timestamp"] = datetime.datetime.now()
        if "host" not in kwargs:
            kwargs["host"] = socket.gethostname()
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
            .order_by(sqlalchemy.asc(flask.current_app.db.func.Date(Drink.timestamp)))
            .group_by(flask.current_app.db.func.Date(Drink.timestamp))
            .all()
        )


class Pay(flask.current_app.db.Model):
    id = flask.current_app.db.Column(flask.current_app.db.Integer, primary_key=True)
    timestamp = flask.current_app.db.Column(flask.current_app.db.DateTime, nullable=False)
    userid = flask.current_app.db.Column(
        flask.current_app.db.Integer,
        flask.current_app.db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    amount = flask.current_app.db.Column(flask.current_app.db.Float, nullable=False)
    host = flask.current_app.db.Column(flask.current_app.db.String(50))

    def __init__(self, *args, **kwargs):
        if "timestamp" not in kwargs:
            kwargs["timestamp"] = datetime.datetime.now()
        if "host" not in kwargs:
            kwargs["host"] = socket.gethostname()
        super().__init__(*args, **kwargs)


def escapefromhex(data):
    if not data:
        return None
    return bytes.fromhex(data)
