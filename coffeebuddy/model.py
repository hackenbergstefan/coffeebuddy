import calendar
import itertools
import socket
import string
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple

import flask
import pandas
import sqlalchemy
from sqlalchemy import Column, ForeignKey, Integer, Table, select, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


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


def db_date_week(column):
    if flask.current_app.db.engine.name == "postgresql":
        return sqlalchemy.func.to_char(column, "YYYY-IW")
    else:
        return sqlalchemy.func.strftime("%Y-%W", column)


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


def escapefromhex(data):
    if not data:
        return None
    return bytes.fromhex(data)


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


coffee_variant_favorites = Table(
    "coffee_variant_favorites",
    Base.metadata,
    Column("user", Integer, ForeignKey("user.id", ondelete="CASCADE")),
    Column(
        "variant",
        Integer,
        ForeignKey("coffee_variant.id", ondelete="CASCADE"),
    ),
)


class User(Base, Serializer):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    tag: Mapped[bytes] = mapped_column(nullable=False, unique=True)
    tag2: Mapped[Optional[bytes]] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column(nullable=False)
    prename: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)
    option_oneswipe: Mapped[bool] = mapped_column(default=False)
    enabled: Mapped[bool] = mapped_column(default=True)
    pays: Mapped[List["Pay"]] = relationship(
        "Pay",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    drinks: Mapped[List["Drink"]] = relationship(
        "Drink",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    variant_favorites = relationship(
        "CoffeeVariant",
        secondary=coffee_variant_favorites,
    )

    @staticmethod
    def by_tag(tag):
        # pylint: disable=singleton-comparison
        return User.query.filter(
            # ruff: noqa: E711
            (User.tag == tag) | ((User.tag2 != None) & (User.tag2 == tag))
        ).first()  # noqa: E711

    @staticmethod
    def by_id(userid):
        return User.query.filter(User.id == userid).first()

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

    @property
    def balance(self):
        return -self.unpayed

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
            f"<User id={self.id} tag={self.tag} tag2={self.tag2} "
            f"name={self.name} prename={self.prename} email={self.email}>"
        )

    def serialize(self):
        serialized = super().serialize()
        serialized["balance"] = (
            self.balance if self not in flask.current_app.db.session.new else 0
        )
        return serialized

    def update_bill(self, newbill):
        flask.current_app.db.session.add(Pay(user=self, amount=self.unpayed - newbill))

    def update_balance(self, newbalance):
        flask.current_app.db.session.add(
            Pay(user=self, amount=newbalance + self.unpayed)
        )

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
    def all_enabled() -> list[str, list["User"]]:
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
            if not data:
                return [], []
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

    @staticmethod
    def drinks_statistics() -> dict["User", list[tuple[str, int]]]:
        """Generate overall statistic for each user."""
        db = flask.current_app.db
        data = db.session.execute(
            db.select(
                User,
                (db.func.Date(Drink.timestamp)).label("date"),
                db.func.count(Drink.id),
            )
            .where(User.enabled)
            .join(Drink, User.id == Drink.userid)
            .group_by(User.id, "date")
            .order_by(User.name)
        ).all()
        df = pandas.DataFrame(
            data,
            columns=("user", "date", "count"),
        )
        df["date"] = pandas.to_datetime(df["date"])
        df = df.pivot(index="date", columns="user", values="count").fillna(0)
        return df.resample("D").sum()

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

    @staticmethod
    def check_consistency():
        """
        Check database for errors.
        """
        db = flask.current_app.db
        all_users = db.session.scalars(db.select(User).where(User.enabled)).all()
        # 1. Check if user pre and post name are distinct
        keyfunc = lambda user: (user.name, user.prename)  # noqa: E731
        for key, users in itertools.groupby(
            sorted(all_users, key=keyfunc),
            key=keyfunc,
        ):
            users = set(users)
            if len(users) > 1:
                raise Exception(f"Duplicate names: {key}: {users!r}")
        # 2. Check if user emails are distinct
        keyfunc = lambda user: user.email  # noqa: E731
        for key, users in itertools.groupby(
            sorted(all_users, key=keyfunc),
            key=keyfunc,
        ):
            users = set(users)
            if len(users) > 1:
                raise Exception(f"Duplicate emails: {key}: {users!r}")
        # 3. Check if all tags are distinct
        keyfunc = lambda tag_user: tag_user[0]  # noqa: E731
        for key, users in itertools.groupby(
            sorted(
                [(u.tag or b"", u) for u in all_users]
                + [(u.tag2 or b"", u) for u in all_users],
                key=keyfunc,
            ),
            key=keyfunc,
        ):
            users = set(users)
            if key and len(users) > 1:
                raise Exception(f"Duplicate tags: {key}: {users!r}")


class Drink(Base, Serializer):
    __tablename__ = "drink"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime]
    price: Mapped[float] = mapped_column(nullable=False)
    userid: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    user: Mapped[User] = relationship("User", back_populates="drinks")
    host: Mapped[str]
    selected_manually: Mapped[bool] = mapped_column(default=False)
    coffeeid: Mapped[Optional[int]] = mapped_column(
        ForeignKey("coffee_variant.id", ondelete="SET NULL"),
        default=None,
    )

    def __init__(self, *args, **kwargs):
        if "timestamp" not in kwargs:
            kwargs["timestamp"] = datetime.now()
        if "host" not in kwargs:
            kwargs["host"] = socket.gethostname()
        super().__init__(*args, **kwargs)

    @staticmethod
    def drinks_vs_days(since):
        previous_date = datetime.now() - since
        data = (
            flask.current_app.db.session.query(
                flask.current_app.db.func.Date(Drink.timestamp),
                flask.current_app.db.func.count(
                    flask.current_app.db.func.Date(Drink.timestamp)
                ),
            )
            .filter(Drink.timestamp > previous_date)
            .order_by(sqlalchemy.asc(flask.current_app.db.func.Date(Drink.timestamp)))
            .group_by(flask.current_app.db.func.Date(Drink.timestamp))
            .all()
        )
        data = {
            day if isinstance(day, str) else day.strftime("%Y-%m-%d"): count
            for day, count in data
        }
        dates_timedelta = [
            (previous_date + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(since.days + 1)
        ]
        return [(date, data.get(date, 0)) for date in dates_timedelta]


class Pay(Base):
    __tablename__ = "pay"
    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(nullable=False)
    userid: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    user: Mapped[User] = relationship("User", back_populates="pays")
    amount: Mapped[float] = mapped_column(nullable=False)
    host: Mapped[str]

    def __init__(self, *args, **kwargs):
        if "timestamp" not in kwargs:
            kwargs["timestamp"] = datetime.now()
        if "host" not in kwargs:
            kwargs["host"] = socket.gethostname()
        super().__init__(*args, **kwargs)

    @staticmethod
    def todays() -> list["Pay"]:
        """Return all payments of today."""
        db = flask.current_app.db
        return db.session.scalars(
            db.select(Pay)
            .where(db.func.Date(Pay.timestamp) == date.today())
            .order_by(Pay.id.asc())
        ).all()


@dataclass
class CoffeeSettings:
    display_name: str
    min: int
    max: int
    step: int
    names: List[str] = None


class CoffeeVariant(Base, Serializer):
    __tablename__ = "coffee_variant"

    id: Mapped[int] = mapped_column(primary_key=True)
    derived_from: Mapped[Optional[int]] = mapped_column(ForeignKey("coffee_variant.id"))
    name: Mapped[str] = mapped_column(unique=True)
    code: Mapped[int]
    icon: Mapped[str]
    strength: Mapped[int]
    grinder_ratio: Mapped[int]
    water: Mapped[int]
    temperature: Mapped[int]
    bypass: Mapped[int]
    milk_foam: Mapped[int]
    milk: Mapped[int]
    price: Mapped[float]

    editable: Mapped[bool] = mapped_column(default=True)
    deleted: Mapped[bool] = mapped_column(default=False)

    settings = {
        "strength": CoffeeSettings(
            "Strength",
            min=1,
            max=5,
            step=1,
            names=["XMild", "Mild", "Normal", "Strong", "XStrong"],
        ),
        "grinder_ratio": CoffeeSettings(
            "Grinder ratio",
            min=0,
            max=4,
            step=1,
            names=["100/0", "75/25", "50/50", "25/75", "0/100"],
        ),
        "water": CoffeeSettings(
            "Water amount",
            min=25,
            max=290,
            step=5,
        ),
        "temperature": CoffeeSettings(
            "Temperature",
            min=0,
            max=2,
            step=1,
            names=["Low", "Normal", "High"],
        ),
        "bypass": CoffeeSettings(
            "Bypass",
            min=0,
            max=580,
            step=5,
        ),
        "milk_foam": CoffeeSettings(
            "Milk foam",
            min=0,
            max=120,
            step=1,
        ),
        "milk": CoffeeSettings(
            "Milk",
            min=0,
            max=120,
            step=1,
        ),
    }

    @staticmethod
    def by_id(coffeeid: int) -> "CoffeeVariant":
        return flask.current_app.db.session.scalar(
            select(CoffeeVariant).where(CoffeeVariant.id == coffeeid)
        )

    def setting_in_percent(self, setting_name: str) -> int:
        setting = self.settings[setting_name]
        return int(
            (getattr(self, setting_name) - setting.min)
            / (setting.max - setting.min)
            * 100
        )

    def setting_display(self, setting_name: str, value: Optional[float] = None) -> str:
        setting = self.settings[setting_name]
        value = getattr(self, setting_name)
        return setting.names[value - setting.min] if setting.names else value

    def __str__(self):
        return (
            f"<CoffeeVariant name={self.name} code={self.code} "
            + " ".join(
                f"{setting_name}={self.setting_display(setting_name)}"
                for setting_name in self.settings
            )
            + ">"
        )

    def __repr__(self):
        return (
            "<CoffeeVariant "
            + " ".join(
                f"{k}={getattr(self, k)}"
                for k in (
                    "id",
                    "name",
                    "code",
                    "icon",
                    "strength",
                    "grinder_ratio",
                    "water",
                    "temperature",
                    "bypass",
                    "milk_foam",
                    "milk",
                    "price",
                    "editable",
                    "deleted",
                )
            )
            + ">"
        )

    def all_for_user(user: User) -> List["CoffeeVariant"]:
        db = flask.current_app.db
        return user.variant_favorites, [
            variant
            for variant in db.session.scalars(
                db.select(CoffeeVariant)
                .where(Drink.coffeeid == CoffeeVariant.id)
                .group_by(CoffeeVariant.id)
                .order_by(db.func.count(Drink.id).desc())
            ).all()
            + db.session.scalars(
                db.select(CoffeeVariant)
                .where(
                    CoffeeVariant.id.not_in(
                        db.select(Drink.coffeeid)
                        .where(Drink.coffeeid != None)
                        .distinct()
                    )
                )
                .order_by(CoffeeVariant.name)
            ).all()
            if variant not in user.variant_favorites
        ]

    @property
    def virtual(self):
        return self.code == -1
