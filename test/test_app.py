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
