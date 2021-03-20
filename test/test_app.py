import datetime
import unittest

import flask
import sqlalchemy

import coffeetag
from coffeetag.model import Drink, User, Pay
from . import TestCoffeetag


class TestUsers(TestCoffeetag):
    def test_non_existing_user(self):
        response = self.client.get('/coffee.html?tag=00', follow_redirects=True)
        self.assertIn(b'Card not found', response.data)

    def test_existing_user(self):
        self.db.session.add(User(tag=b'\x01\x02\x03', name='Mustermann', prename='Max'))
        self.db.session.commit()
        response = self.client.get('/coffee.html?tag=010203')
        self.assertEqual(response.status_code, 200)

    def test_drink_coffee(self):
        user1 = User(tag=b'\x01\x02\x03', name='Mustermann', prename='Max')
        user2 = User(tag=b'\x03\x04\x05', name='Doe', prename='Jane')
        self.db.session.add(user1)
        self.db.session.add(user2)
        self.db.session.commit()
        response = self.client.post('/coffee.html?tag=010203', data=dict(coffee='coffee'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(user1.coffees), 1)
        self.assertEqual(len(user1.coffees_today), 1)
        response = self.client.post('/coffee.html?tag=030405', data=dict(coffee='coffee'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(user2.coffees), 1)

    def test_drinks_today(self):
        user1 = User(tag=b'\x01\x02\x03', name='Mustermann', prename='Max')
        user2 = User(tag=b'\x03\x04\x05', name='Doe', prename='Jane')
        self.db.session.add(user1)
        self.db.session.add(user2)
        self.db.session.commit()

        user1.coffees.append(Drink(price=30))
        user1.coffees.append(Drink(price=30, timestamp=datetime.datetime.now() - datetime.timedelta(days=1)))
        user2.coffees.append(Drink(price=30))

        self.assertEqual(len(user1.coffees), 2)
        self.assertEqual(len(user1.coffees_today), 1)
        self.assertEqual(len(user2.coffees), 1)

    def test_pay(self):
        user = User(tag=b'\x01\x02\x03', name='Mustermann', prename='Max')
        self.db.session.add(user)
        self.db.session.commit()

        user.coffees.append(Drink(price=30))
        user.coffees.append(Drink(price=30))
        user.coffees.append(Drink(price=30))
        user.pays.append(Pay(amount=60))
        self.db.session.commit()

        self.assertEqual(user.unpayed, 30)

    def test_edituser(self):
        response = self.client.post('/edituser.html', data=dict(
            tag='01 02 03 04',
            last_name='Mustermann',
            first_name='Max',
        ))
        self.assertEqual(response.status_code, 302)
        users = User.query.all()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].tag, b'\x01\x02\x03\x04')
        self.assertEqual(users[0].name, 'Mustermann')
        self.assertEqual(users[0].prename, 'Max')

    def test_add_existing_user_fails(self):
        response = self.client.post('/edituser.html', data=dict(
            tag='01 02 03 04',
            last_name='Mustermann',
            first_name='Max',
        ))
        self.assertEqual(response.status_code, 302)
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            self.client.post('/edituser.html', data=dict(
                tag='01 02 03 04',
                last_name='Mustermann',
                first_name='Max',
            ))
        self.db.session.rollback()
