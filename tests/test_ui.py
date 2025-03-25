import time

from selenium.webdriver.support import expected_conditions as ec

from .conftest import HOST, CoffeeBuddyWebDriver


def test_welcome(web: CoffeeBuddyWebDriver, user):
    web.get(HOST)
    web.nav("selectuser")
    assert web.current_url == f"{HOST}/selectuser.html"
    users = web.find_elements_css(".item")
    assert "Mustermann Max" in [user.text for user in users]

    web.nav("back")
    assert web.current_url == f"{HOST}/"


def test_selectuser(web: CoffeeBuddyWebDriver, user):
    web.get(f"{HOST}/selectuser.html")
    users = web.find_elements_css(".item")
    index = [user.text for user in users].index("Mustermann Max")
    assert index >= 0
    users[index].click()
    assert (
        web.current_url == f"{HOST}/coffee.html?tag={user['tag']}&manually&can-oneswipe"
    )


def test_coffee(web: CoffeeBuddyWebDriver, user):
    web.get(f"{HOST}/coffee.html?tag={user['tag']}")
    assert web.current_url == f"{HOST}/coffee.html?tag={user['tag']}"

    web.nav("pay")
    assert web.current_url == f"{HOST}/pay.html?tag={user['tag']}"
    web.nav("back")

    web.nav("edituser")
    assert web.current_url == f"{HOST}/edituser.html?id={user['id']}"
    web.nav("back")

    web.nav("stats")
    assert web.current_url == f"{HOST}/stats.html?tag={user['tag']}"
    web.nav("back")

    el = web.find_element_css(".coffee-icon-container")
    coffee_id = el.get_attribute("coffee-id")
    current_url = web.current_url
    el.click()
    web.wait(ec.url_changes(current_url))
    assert web.current_url == (
        f"{HOST}/brew.html?tag={user['tag']}&coffeeid={coffee_id}"
    )
    el = web.find_element_css("button[name='no']")
    current_url = web.current_url
    el.click()
    web.wait(ec.url_changes(current_url))
    web.nav("logout")
    assert web.current_url == f"{HOST}/"


def test_pay(web: CoffeeBuddyWebDriver, user):
    balance = 0
    assert user["balance"] == balance

    for i, amount in enumerate((5, 10, 20, 50, "X")):
        web.get(f"{HOST}/pay.html?tag={user['tag']}")
        pay = web.find_elements_css("button.btn-pay")[i]
        assert str(amount) == pay.text
        if isinstance(amount, int):
            pay.click()
        else:
            pay.click()
            amount = 5.23
            el = web.find_element_css("#simple-keyboard-input")
            web.wait(ec.visibility_of(el))
            el.send_keys(f"{amount:.2f}")
            web.find_element_css(".hg-button-enter").click()
        balance += amount

        modal = web.find_element_css("#modal-confirm")
        web.wait(ec.visibility_of(modal))
        web.wait(
            ec.element_to_be_clickable(web.find_element_css("#modal-confirm button"))
        ).click()
        web.wait(ec.invisibility_of_element(modal))
        assert web.api("user/get", id=user["id"])["balance"] == balance


def test_pay_abort(web: CoffeeBuddyWebDriver, user):
    assert user["balance"] == 0
    web.get(f"{HOST}/pay.html?tag={user['tag']}")
    web.find_element_css("button.btn-pay").click()
    web.wait(ec.visibility_of(web.find_element_css("#modal-confirm")))
    web.wait(
        ec.element_to_be_clickable(web.find_elements_css("#modal-confirm button")[-1])
    ).click()

    assert web.api("user/get", id=user["id"])["balance"] == 0


def test_edituser(web: CoffeeBuddyWebDriver, user):
    web.get(f"{HOST}/edituser.html?id={user['id']}")

    el = web.find_element_css("input[name='tag']")
    el.clear()
    el.send_keys("ff ff ff ff")
    web.find_element_css("button[name='save']").click()
    web.wait(ec.visibility_of(web.find_element_css("#modal-updated")))

    assert web.api("user/get", id=user["id"])["tag"] == "ffffffff"


def test_edituser_duplicate_tag_fails(web: CoffeeBuddyWebDriver):
    users = web.api("user/get")

    web.get(f"{HOST}/edituser.html?id={users[0]['id']}")
    el = web.find_element_css("input[name='tag']")
    el.clear()
    el.send_keys(users[1]["tag"])
    web.find_element_css("button[name='save']").click()
    web.wait(ec.visibility_of(web.find_element_css("#modal-error")))

    # Check that user was not changed
    assert web.api("user/get", id=users[0]["id"])["tag"] == users[0]["tag"]


def test_brew(web: CoffeeBuddyWebDriver, user):
    web.get(f"{HOST}/brew.html?tag={user['tag']}&coffeeid=1")
    web.find_element_css("button[name='yes']").click()
    web.wait(ec.visibility_of(web.find_element_css("#brew-brewing")))
    time.sleep(1)
    assert web.current_url == f"{HOST}/coffee.html?tag={user['tag']}"
    assert len(web.api("user/drinks", id=user["id"])) == 1
    assert web.api("user/get", id=user["id"])["balance"] < 0


def test_screenshots(web: CoffeeBuddyWebDriver):
    web.get(f"{HOST}/")
    web.save_screenshot("doc/welcome.png")

    web.get(f"{HOST}/selectuser.html")
    web.save_screenshot("doc/selectuser.png")

    web.get(f"{HOST}/coffee.html?tag=01")
    web.save_screenshot("doc/coffee.png")

    web.get(f"{HOST}/brew.html?coffeeid=1&tag=01")
    web.save_screenshot("doc/brew.png")

    web.get(f"{HOST}/brew.html?coffeeid=1&tag=01")
    web.save_screenshot("doc/brew.png")

    web.get(f"{HOST}/editcoffee.html?derive=1&tag=01")
    web.save_screenshot("doc/editcoffee.png")

    web.get(f"{HOST}/edituser.html?tag=01")
    web.save_screenshot("doc/edituser.png")

    web.get(f"{HOST}/stats.html?tag=01")
    web.save_screenshot("doc/stats.png")

    web.get(f"{HOST}/pay.html?tag=01")
    web.save_screenshot("doc/pay.png")

    web.get(f"{HOST}/cardnotfound.html?uuid=01020304")
    web.save_screenshot("doc/cardnotfound.png")
