import datetime

from coffeetag import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.LargeBinary)
    name = db.Column(db.String(50))
    prename = db.Column(db.String(50))

    def coffees_today(self):
        return Drink.query.join(User.coffees, aliased=True).filter(
            self.id == Drink.userid and
            db.DATE(Drink.timestamp) == datetime.date.today()
        ).all()


class Drink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    userid = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('coffees', lazy=True))

    def __init__(self, *args, **kwargs):
        if 'timestamp' not in kwargs:
            kwargs['timestamp'] = datetime.datetime.now()
        super().__init__(*args, **kwargs)
