import unittest

from . import TestCoffeetag
from coffeetag.user import User


class TestUsers(TestCoffeetag):
    def test_non_existing_user(self):
        response = self.client.get('/coffee.html?tag=0')
        self.assertEqual(response.status_code, 404)

    def test_existing_user(self):
        self.db.add(User(tag=b'123', name='Mustermann', prename='Max'))
        self.db.commit()
        response = self.client.get('/coffee.html?tag=123')
        self.assertEqual(response.status_code, 200)

    def test_drink_coffee(self):
        user = User(tag=b'123', name='Mustermann', prename='Max')
        self.db.add(user)
        self.db.commit()
        response = self.client.post('/coffee.html?tag=123', data=dict(coffee='coffee'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(user.coffees, 1)
