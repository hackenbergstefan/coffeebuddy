import unittest
import coffeetag

class TestCoffeetag(unittest.TestCase):
    def setUp(self):
        coffeetag.app.testing = True
        coffeetag.create_app()

        self.app = coffeetag.app
        self.client = self.app.test_client().__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
