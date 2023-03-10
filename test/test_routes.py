import json

from . import TestCoffeebuddy


class TestRouteEdituser(TestCoffeebuddy):
    def test_adduser_tag1(self):
        from coffeebuddy.model import User

        response = self.client.post(
            "/edituser.html",
            data=dict(
                id="",
                tag="01 02 03 04",
                tag2="",
                last_name="Mustermann",
                first_name="Max",
                email="Max.Mustermann@example.com",
            ),
        )
        self.assertEqual(response.status_code, 302)
        users = User.query.all()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].tag, b"\x01\x02\x03\x04")
        self.assertEqual(users[0].tag2, None)
        self.assertEqual(users[0].name, "Mustermann")
        self.assertEqual(users[0].prename, "Max")
        self.assertEqual(users[0].option_oneswipe, False)

    def test_adduser_tag1_tag2(self):
        from coffeebuddy.model import User

        response = self.client.post(
            "/edituser.html",
            data=dict(
                id="",
                tag="01 02 03 04",
                tag2="01 02 03 04",
                last_name="Mustermann",
                first_name="Max",
                email="Max.Mustermann@example.com",
            ),
        )
        self.assertEqual(response.status_code, 302)
        users = User.query.all()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].tag, b"\x01\x02\x03\x04")
        self.assertEqual(users[0].tag2, b"\x01\x02\x03\x04")
        self.assertEqual(users[0].name, "Mustermann")
        self.assertEqual(users[0].prename, "Max")
        self.assertEqual(users[0].option_oneswipe, False)

    def test_adduser_tag2_fails(self):
        response = self.client.post(
            "/edituser.html",
            data=dict(
                id="",
                tag="",
                tag2="01 02 03 04",
                last_name="Mustermann",
                first_name="Max",
                email="Max.Mustermann@example.com",
            ),
        )
        self.assertEqual(response.status_code, 400)

    def test_edituser_nochange(self):
        user1, _ = self.add_default_user()

        self.client.post(
            "/edituser.html",
            data=dict(
                id=user1.id,
                tag=user1.tag.hex(),
                tag2=(user1.tag2 or b"").hex(),
                last_name=user1.name,
                first_name=user1.prename,
                email=user1.email,
            ),
        )

        self.assertEqual(user1.id, 1)
        self.assertEqual(user1.tag, b"\x01\x02\x03\x04")
        self.assertEqual(user1.tag2, None)
        self.assertEqual(user1.name, "Mustermann")
        self.assertEqual(user1.prename, "Max")
        self.assertEqual(user1.option_oneswipe, False)
        self.assertEqual(len(user1.drinks), 0)
        self.assertEqual(len(user1.pays), 0)

    def test_edituser_update_tag(self):
        user1, _ = self.add_default_user()

        self.client.post(
            "/edituser.html",
            data=dict(
                id=user1.id,
                tag="ff ff ff ff",
                tag2="",
                last_name=user1.name,
                first_name=user1.prename,
                email=user1.email,
            ),
        )

        self.assertEqual(user1.id, 1)
        self.assertEqual(user1.tag, b"\xff\xff\xff\xff")
        self.assertEqual(user1.tag2, None)
        self.assertEqual(user1.name, "Mustermann")
        self.assertEqual(user1.prename, "Max")
        self.assertEqual(user1.option_oneswipe, False)
        self.assertEqual(len(user1.drinks), 0)
        self.assertEqual(len(user1.pays), 0)

    def test_edituser_update_tag2(self):
        user1, _ = self.add_default_user()

        self.client.post(
            "/edituser.html",
            data=dict(
                id=user1.id,
                tag=user1.tag.hex(),
                tag2="ff ff ff ff",
                last_name=user1.name,
                first_name=user1.prename,
                email=user1.email,
            ),
        )

        self.assertEqual(user1.id, 1)
        self.assertEqual(user1.tag, b"\x01\x02\x03\x04")
        self.assertEqual(user1.tag2, b"\xff\xff\xff\xff")
        self.assertEqual(user1.name, "Mustermann")
        self.assertEqual(user1.prename, "Max")
        self.assertEqual(user1.option_oneswipe, False)
        self.assertEqual(len(user1.drinks), 0)
        self.assertEqual(len(user1.pays), 0)


class TestRouteCoffee(TestCoffeebuddy):
    def test_non_existing_user(self):
        response = self.client.get("/coffee.html?tag=00", follow_redirects=True)
        self.assertIn(b"Card not found", response.data)

    def test_existing_user(self):
        self.add_default_user()
        response = self.client.get("/coffee.html?tag=01020304")
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        self.add_default_user()
        response = self.client.post("/coffee.html?tag=01020304", data=dict(logout=""))
        self.assertEqual(response.status_code, 302)


class TestRouteOneSwipe(TestCoffeebuddy):
    def test(self):
        user, _ = self.add_default_user()
        response = self.client.post(f"/oneswipe.html?tag={user.tag.hex()}", data=dict(coffee=True))
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(user.drinks), 0)


class TestRouteWelcome(TestCoffeebuddy):
    def test(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)


class TestRoutePay(TestCoffeebuddy):
    def test(self):
        user, _ = self.add_default_user()
        response = self.client.post(f"/pay.html?tag={user.tag.hex()}", data=dict(amount=1))
        self.assertEqual(response.status_code, 302)
        self.assertGreater(len(user.pays), 0)


class TestRouteApi(TestCoffeebuddy):
    def test_get_users(self):
        user1, user2 = self.add_default_user()
        response = self.client.post("api/get_users")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), [user1.serialize(), user2.serialize()])

    def test_set_user(self):
        user1, _ = self.add_default_user()
        for arg in ("email", "name", "prename", "tag", "tag2"):
            with self.subTest(arg=arg):
                response = self.client.post(
                    "api/set_user",
                    data=json.dumps({"id": user1.id, arg: "01020304"}),
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(json.loads(response.data), user1.serialize())

    def test_check_email(self):
        response = self.client.post(
            "api/check_email",
            data=json.dumps({"email": "jane.doe@example.com"}),
            content_type="application/json",
        )
        self.assertIn(response.status_code, (200, 404))
