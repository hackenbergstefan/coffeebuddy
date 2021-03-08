import datetime

from sqlalchemy import Column, Integer, String, LargeBinary, ForeignKey, DateTime, cast, Date, func
from sqlalchemy.orm import relationship
from coffeetag.database import Base


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    tag = Column(LargeBinary)
    name = Column(String(50))
    prename = Column(String(50))
    coffees = relationship('Drink')

    def coffees_today(self):
        return Drink.query.join(User.coffees, aliased=True).filter(
            func.DATE(Drink.timestamp) == datetime.date.today()
        ).all()


class Drink(Base):
    __tablename__ = 'drink'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    userid = Column(Integer, ForeignKey('user.id'))
    user = relationship('User', back_populates='coffees')

    def __init__(self, *args, **kwargs):
        if 'timestamp' not in kwargs:
            kwargs['timestamp'] = datetime.datetime.now()
        super().__init__(*args, **kwargs)
