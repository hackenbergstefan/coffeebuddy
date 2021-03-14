import datetime
import unittest

import flask

import coffeetag
from coffeetag.model import Drink, User
from . import TestCoffeetag


class TestUsers(TestCoffeetag):
    def test_non_existing_user(self):
        response = self.client.get('/coffee.html?tag=0')
        self.assertEqual(response.status_code, 404)

    def test_existing_user(self):
        self.db.session.add(User(tag=b'123', name='Mustermann', prename='Max'))
        self.db.session.commit()
        response = self.client.get('/coffee.html?tag=123')
        self.assertEqual(response.status_code, 200)

    def test_drink_coffee(self):
        user1 = User(tag=b'123', name='Mustermann', prename='Max')
        user2 = User(tag=b'345', name='Doe', prename='Jane')
        self.db.session.add(user1)
        self.db.session.add(user2)
        self.db.session.commit()
        response = self.client.post('/coffee.html?tag=123', data=dict(coffee='coffee'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(user1.coffees), 1)
        self.assertEqual(len(user1.coffees_today()), 1)
        response = self.client.post('/coffee.html?tag=345', data=dict(coffee='coffee'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(user2.coffees), 1)

    def test_drinks_today(self):
        user1 = User(tag=b'123', name='Mustermann', prename='Max')
        user2 = User(tag=b'345', name='Doe', prename='Jane')
        self.db.session.add(user1)
        self.db.session.add(user2)
        self.db.session.commit()

        user1.coffees.append(Drink())
        user1.coffees.append(Drink(timestamp=datetime.datetime.now() - datetime.timedelta(days=1)))
        user2.coffees.append(Drink())

        self.assertEqual(len(user1.coffees), 2)
        self.assertEqual(len(user1.coffees_today()), 2)
        self.assertEqual(len(user2.coffees), 1)
