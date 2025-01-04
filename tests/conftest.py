import os
import subprocess
import time

import pytest
import requests
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

import coffeebuddy

HOST = "http://127.0.0.1:5000"


class CoffeeBuddyWebDriver(Chrome):
    def nav(self, name: str):
        """
        Click on a button in the nav bar with the given name.
        """
        self.find_element(By.CSS_SELECTOR, f"button[name='{name}']").click()

    def find_elements_css(self, value=None):
        return super().find_elements(By.CSS_SELECTOR, value)

    def find_element_css(self, value):
        return super().find_elements(By.CSS_SELECTOR, value)[0]

    def api(self, endpoint: str, **kwargs):
        return requests.request("GET", f"{HOST}/api/{endpoint}", params=kwargs).json()

    def wait(
        self,
        condition,
        timeout: int = 2,
    ):
        return WebDriverWait(self, timeout).until(condition)


@pytest.fixture
def app():
    app = coffeebuddy.create_app({"TESTING": True})

    with app.app_context():
        coffeebuddy.init_app_context(app)

        yield app


def start_server(config: dict, verbose: bool = False):
    proc = subprocess.Popen(
        ("python", "./bin/run.py"),
        stdout=None if verbose else subprocess.DEVNULL,
        stderr=None if verbose else subprocess.DEVNULL,
        env=os.environ | {"FLASK_CONFIG": str(config)},
    )
    # Wait until socket is open
    while True:
        try:
            requests.get(HOST)
            break
        except requests.ConnectionError:
            time.sleep(0.1)
    return proc


@pytest.fixture(scope="session")
def server(request, pytestconfig):
    proc = start_server(
        config={
            "TESTING": True,
            "PREFILLED": True,
            "COFFEEMAKER": {"mock": 0.1},
        },
        verbose=pytestconfig.get_verbosity() > 1,
    )
    request.session.proc = proc
    yield
    proc.terminate()
    proc.wait()
    proc.kill()


@pytest.fixture(scope="session")
def web(server):
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-using")
    options.add_argument("--disable-extensions")
    options.add_argument("--remote-debugging-port=9222")
    yield CoffeeBuddyWebDriver(options=options)


@pytest.fixture
def user(server):
    response = requests.get(
        f"{HOST}/api/user/set",
        params={
            "tag": "01020304",
            "tag2": None,
            "name": "Mustermann",
            "prename": "Max",
            "email": "Max.Mustermann@example.com",
        },
    )
    user_id = response.json()["id"]
    assert response.status_code == 200
    yield response.json()
    requests.get(f"{HOST}/api/user/del", params={"id": user_id})
    response = requests.get(f"{HOST}/api/user/get", params={"id": user_id})
    assert response.status_code == 400
