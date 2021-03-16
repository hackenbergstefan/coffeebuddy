import datetime

from coffeetag import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.LargeBinary, nullable=False, unique=True)
    name = db.Column(db.String(50), nullable=False)
    prename = db.Column(db.String(50), nullable=False)

    @property
    def coffees_today(self):
        return Drink.query.filter(
            self.id == Drink.userid and
            db.func.Date(Drink.timestamp) == datetime.date.today()
        ).all()

    @property
    def unpayed(self):
        # TODO: Fast enough?
        return sum(c.price for c in self.coffees) - sum(p.amount for p in self.pays)

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
