import unittest
import flask
import coffeetag


class TestCoffeetag(unittest.TestCase):
    def setUp(self):
        self.app, _ = coffeetag.create_app({'TESTING': True})
        self.client = self.app.test_client().__enter__()
        self.ctx = self.app.app_context().__enter__()
        self.db = flask.g.db = coffeetag.init_db(self.app)

    def tearDown(self):
        self.truncate_all()
        self.ctx.__exit__(None, None, None)
        self.client.__exit__(None, None, None)

    def truncate_all(self):
        for table in reversed(self.db.metadata.sorted_tables):
            self.db.session.execute(table.delete())
        self.db.session.commit()
