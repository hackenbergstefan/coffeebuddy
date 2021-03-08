import unittest

from . import TestCoffeetag


class TestUsers(TestCoffeetag):
    def test_non_existing_user(self):
        response = self.client.get('/coffee.html?tag=0')
        self.assertEqual(response.status_code, 404)

    def test_existing_user(self):
        from coffeetag.model import User
        self.app.db.add(User(tag=b'123', name='Mustermann', prename='Max'))
        self.app.db.commit()
        response = self.client.get('/coffee.html?tag=123')
        self.assertEqual(response.status_code, 200)

    def test_drink_coffee(self):
        from coffeetag.model import User
        user = User(tag=b'123', name='Mustermann', prename='Max')
        self.app.db.add(user)
        self.app.db.commit()
        response = self.client.post('/coffee.html?tag=123', data=dict(coffee='coffee'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(user.coffees), 1)
        self.assertEqual(len(user.coffees_today()), 1)
