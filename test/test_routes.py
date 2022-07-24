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
                initial_bill="",
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
                initial_bill="",
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
                initial_bill="",
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
                initial_bill="",
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
                initial_bill="",
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
                initial_bill="",
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
