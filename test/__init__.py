import unittest
import flask
import coffeebuddy

from coffeebuddy.model import User


class TestCoffeebuddy(unittest.TestCase):
    def setUp(self):
        self.app, _ = coffeebuddy.create_app({'TESTING': True})
        self.client = self.app.test_client().__enter__()
        self.ctx = self.app.app_context().__enter__()
        self.db = flask.g.db = coffeebuddy.init_db(self.app)

    def tearDown(self):
        self.truncate_all()
        self.ctx.__exit__(None, None, None)
        self.client.__exit__(None, None, None)

    def truncate_all(self):
        for table in reversed(self.db.metadata.sorted_tables):
            self.db.session.execute(table.delete())
        self.db.session.commit()

    def add_default_user(self):
        user1 = User(tag=b'\x01\x02\x03', name='Mustermann', prename='Max')
        self.db.session.add(user1)
        user2 = User(tag=b'\x04\x05\x06', name='Doe', prename='Jane')
        self.db.session.add(user2)
        self.db.session.commit()
        return user1, user2
