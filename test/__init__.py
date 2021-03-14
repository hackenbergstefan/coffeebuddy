import unittest
import flask
import coffeetag

class TestCoffeetag(unittest.TestCase):
    def setUp(self):
        self.app = coffeetag.create_app({'TESTING': True})
        self.client = self.app.test_client().__enter__()
        self.ctx = self.app.app_context().__enter__()
        self.db = flask.g.db = coffeetag.init_db(self.app)

    def tearDown(self):
        self.ctx.__exit__(None, None, None)
        self.client.__exit__(None, None, None)
