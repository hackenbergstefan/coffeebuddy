import calendar
import socket
import string
from datetime import date, datetime, timedelta
from typing import List, Tuple

import flask
import sqlalchemy
from sqlalchemy import text


def db_weekday(column) -> str:
    """Helper to extract weekday for different database backends"""
    if flask.current_app.db.engine.name == "postgresql":
        return sqlalchemy.func.extract("dow", column)
    else:
        return sqlalchemy.func.strftime("%w", column)


def db_date_format(column):
    if flask.current_app.db.engine.name == "postgresql":
        return sqlalchemy.func.to_char(column, "YYYY-MM-DD")
    else:
        return sqlalchemy.func.strftime("%Y-%m-%d", column)


def weekday(number):
    """
    Helper to return the name of the weekday for given day number.
    0: Sunday
    1: Monday
    ..
    """
    if number == 0:
        return calendar.day_name[6]
    else:
        return calendar.day_name[number - 1]


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
    tag = flask.current_app.db.Column(
        flask.current_app.db.LargeBinary, nullable=False, unique=True
    )
    tag2 = flask.current_app.db.Column(
        flask.current_app.db.LargeBinary, unique=True, default=None
    )
    name = flask.current_app.db.Column(flask.current_app.db.String(50), nullable=False)
    prename = flask.current_app.db.Column(
        flask.current_app.db.String(50), nullable=False
    )
    email = flask.current_app.db.Column(flask.current_app.db.String(50), nullable=False)
    option_oneswipe = flask.current_app.db.Column(
        flask.current_app.db.Boolean, default=False
    )
    enabled = flask.current_app.db.Column(flask.current_app.db.Boolean, default=True)
    pays = flask.current_app.db.relationship(
        "Pay", backref="user", cascade="all, delete"
    )
    drinks = flask.current_app.db.relationship(
        "Drink", backref="user", cascade="all, delete"
    )

    @staticmethod
    def by_tag(tag):
        # pylint: disable=singleton-comparison
        return User.query.filter(
            # ruff: noqa: E711
            (User.tag == tag) | ((User.tag2 != None) & (User.tag2 == tag))
        ).first()  # noqa: E711

    @property
    def drinks_today(self):
        return (
            Drink.query.filter(Drink.user == self)
            .filter(flask.current_app.db.func.Date(Drink.timestamp) == date.today())
            .all()
        )

    @property
    def unpayed(self):
        db = flask.current_app.db
        return (
            db.session.scalar(
                db.select(db.func.sum(Drink.price)).where(Drink.userid == self.id),
            )
            or 0.0
        ) - (
            db.session.scalar(
                db.select(db.func.sum(Pay.amount)).where(Pay.userid == self.id),
            )
            or 0.0
        )

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
                flask.current_app.db.func.count(
                    flask.current_app.db.func.Date(Drink.timestamp)
                ),
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
            for tup in flask.current_app.db.session.query(
                flask.current_app.db.func.Date(Drink.timestamp)
            )
            .filter(self.id == Drink.userid)
            .distinct()
            .order_by(Drink.timestamp)
        )

    def __str__(self):
        return f"{self.prename} {self.name} ({self.email})"

    def __repr__(self):
        return (
            f"<User tag={self.tag} tag2={self.tag2} "
            f"name={self.name} prename={self.prename} email={self.email}>"
        )

    def serialize(self):
        serialized = super().serialize()
        serialized["unpayed"] = self.unpayed
        return serialized

    def update_bill(self, newbill):
        flask.current_app.db.session.add(Pay(user=self, amount=self.unpayed - newbill))

    @staticmethod
    def top_selected_manually(
        limit: int = 5,
        since=timedelta(weeks=4),
    ) -> List["User"]:
        db = flask.current_app.db
        now = date.today()
        since = (
            datetime.combine(now - timedelta(now.weekday()), datetime.min.time())
            - since
        )
        return db.session.scalars(
            db.select(User)
            .where(
                (Drink.userid == User.id)
                & (Drink.host == socket.gethostname())
                & (Drink.selected_manually)
                & (db.func.Date(Drink.timestamp) >= since)
            )
            .group_by(User.id)
            .limit(limit)
            .order_by(db.func.count(Drink.selected_manually).desc())
        ).all()

    @staticmethod
    def all_enabled() -> List["User"]:
        db = flask.current_app.db
        users = [
            (
                letter,
                db.session.scalars(
                    db.select(User)
                    .filter(db.func.upper(User.name).startswith(letter) & User.enabled)
                    .order_by(User.name)
                ).all(),
            )
            for letter in string.ascii_uppercase
        ]
        return [
            (letter, users_letter)
            for (letter, users_letter) in users
            if len(users_letter) > 0
        ]

    def drinks_this_week(self) -> Tuple[List[str], List[int]]:
        db = flask.current_app.db
        now = date.today()
        start_of_week = datetime.combine(
            now - timedelta(now.weekday()), datetime.min.time()
        )

        data = tuple(
            zip(
                *db.session.execute(
                    db.select(
                        db_weekday(Drink.timestamp).label("weekday"),
                        db.func.count(db.func.Date(Drink.timestamp)),
                    )
                    .where(Drink.userid == self.id)
                    .where(Drink.timestamp >= start_of_week)
                    .group_by("weekday")
                    .order_by("weekday")
                ).all()
            )
        )

        if not data:
            return [], []
        return [weekday(int(i)) for i in data[0]], list(data[1])

    def drinks_last_weeks(
        self,
        since=timedelta(weeks=12),
        group_by="week",
    ) -> Tuple[List[str], List[int]]:
        db = flask.current_app.db
        now = date.today()
        number_of_weeks = since.days / 7
        since = (
            datetime.combine(now - timedelta(now.weekday()), datetime.min.time())
            - since
        )
        if group_by == "week":
            data = tuple(
                zip(
                    *db.session.execute(
                        db.select(
                            db_weekday(Drink.timestamp).label("weekday"),
                            db.func.count(db.func.Date(Drink.timestamp))
                            / number_of_weeks,
                        )
                        .where(
                            (Drink.userid == self.id)
                            & (db.func.Date(Drink.timestamp) >= since)
                        )
                        .group_by("weekday")
                        .order_by("weekday")
                    ).all()
                )
            )
            return [weekday(int(i)) for i in data[0]], list(data[1])
        elif group_by == "day":
            return tuple(
                zip(
                    *db.session.execute(
                        db.select(
                            db_date_format(db.func.Date(Drink.timestamp)),
                            db.func.count(db.func.Date(Drink.timestamp)),
                        )
                        .where(
                            (Drink.userid == self.id)
                            & (db.func.Date(Drink.timestamp) >= since)
                        )
                        .group_by(db.func.Date(Drink.timestamp))
                        .order_by(db.func.Date(Drink.timestamp))
                    ).all()
                )
            )

    @staticmethod
    def drinks_last_weeks_all(since=timedelta(weeks=12)) -> Tuple[List[str], List[int]]:
        db = flask.current_app.db

        now = date.today()
        number_of_weeks = since.days / 7
        since = (
            datetime.combine(now - timedelta(now.weekday()), datetime.min.time())
            - since
        )

        number_of_consumers = db.session.scalar(
            db.select(db.func.count(Drink.userid.distinct())).where(
                db.func.Date(Drink.timestamp) >= since
            )
        )

        data = tuple(
            zip(
                *db.session.execute(
                    db.select(
                        db_weekday(Drink.timestamp).label("weekday"),
                        db.func.count("*") / number_of_consumers / number_of_weeks,
                    )
                    .where(db.func.Date(Drink.timestamp) >= since)
                    .group_by("weekday")
                    .order_by("weekday")
                ).all()
            )
        )
        return [weekday(int(i)) for i in data[0]], list(data[1])

    def drinks_avg_today(self) -> float:
        db = flask.current_app.db
        today_weekday = str(date.today().isoweekday() % 7)

        data = db.session.scalars(
            db.select(db.func.count("*"))
            .where(Drink.userid == self.id)
            .where(db_weekday(db.func.Date(Drink.timestamp)) == today_weekday)
            .group_by(db.func.Date(Drink.timestamp))
        ).all()
        return sum(data) / len(data) if data else 0


class Drink(flask.current_app.db.Model):
    id = flask.current_app.db.Column(flask.current_app.db.Integer, primary_key=True)
    timestamp = flask.current_app.db.Column(flask.current_app.db.DateTime)
    price = flask.current_app.db.Column(flask.current_app.db.Float, nullable=False)
    userid = flask.current_app.db.Column(
        flask.current_app.db.Integer,
        flask.current_app.db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    host = flask.current_app.db.Column(flask.current_app.db.String(50))
    selected_manually = flask.current_app.db.Column(
        flask.current_app.db.Boolean, default=False
    )

    def __init__(self, *args, **kwargs):
        if "timestamp" not in kwargs:
            kwargs["timestamp"] = datetime.now()
        if "host" not in kwargs:
            kwargs["host"] = socket.gethostname()
        super().__init__(*args, **kwargs)

    @staticmethod
    def drinks_vs_days(timedelta):
        return (
            flask.current_app.db.session.query(
                flask.current_app.db.func.count(
                    flask.current_app.db.func.Date(Drink.timestamp)
                ),
                flask.current_app.db.func.Date(Drink.timestamp),
            )
            .filter(Drink.timestamp > datetime.now() - timedelta)
            .order_by(sqlalchemy.asc(flask.current_app.db.func.Date(Drink.timestamp)))
            .group_by(flask.current_app.db.func.Date(Drink.timestamp))
            .all()
        )


class Pay(flask.current_app.db.Model):
    id = flask.current_app.db.Column(flask.current_app.db.Integer, primary_key=True)
    timestamp = flask.current_app.db.Column(
        flask.current_app.db.DateTime, nullable=False
    )
    userid = flask.current_app.db.Column(
        flask.current_app.db.Integer,
        flask.current_app.db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    amount = flask.current_app.db.Column(flask.current_app.db.Float, nullable=False)
    host = flask.current_app.db.Column(flask.current_app.db.String(50))

    def __init__(self, *args, **kwargs):
        if "timestamp" not in kwargs:
            kwargs["timestamp"] = datetime.now()
        if "host" not in kwargs:
            kwargs["host"] = socket.gethostname()
        super().__init__(*args, **kwargs)


def escapefromhex(data):
    if not data:
        return None
    return bytes.fromhex(data)
