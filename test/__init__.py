import unittest

import coffeetag
import coffeetag.app
import coffeetag.database
from coffeetag.user import User


class TestCoffeetag(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.app = coffeetag.app.app
        self.app.testing = True

    def setUp(self):
        self.client = self.app.test_client().__enter__()
        User.query.delete()
        self.db = coffeetag.database.db_session

    def tearDown(self):
        self.client.__exit__(None, None, None)
