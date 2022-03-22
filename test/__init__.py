import unittest

import flask

import coffeebuddy


class TestCoffeebuddy(unittest.TestCase):
    def setUp(self):
        self.app = coffeebuddy.create_app({"TESTING": True})
        self.client = self.app.test_client().__enter__()
        self.ctx = self.app.app_context().__enter__()
        coffeebuddy.init_db()
        coffeebuddy.init_app_context()
        self.db = flask.current_app.db
        self.db.create_all()

    def tearDown(self):
        self.truncate_all()
        self.ctx.__exit__(None, None, None)
        self.client.__exit__(None, None, None)

    def truncate_all(self):
        self.db.session.rollback()
        for table in reversed(self.db.metadata.sorted_tables):
            self.db.session.execute(table.delete())
        self.db.session.commit()

    def add_default_user(self):
        from coffeebuddy.model import User

        user1 = User(tag=b"\x01\x02\x03\x04", name="Mustermann", prename="Max")
        self.db.session.add(user1)
        user2 = User(tag=b"\x05\x06\x07\x08", name="Doe", prename="Jane")
        self.db.session.add(user2)
        self.db.session.commit()
        return user1, user2
