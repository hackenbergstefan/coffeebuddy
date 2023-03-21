import sqlalchemy.exc

from . import TestCoffeebuddy


class TestModelUser(TestCoffeebuddy):
    def test_add_user_mandatory_fields(self):
        from coffeebuddy.model import User

        self.db.session.add(
            User(
                tag=b"\x00\x00\x00\x00",
                prename="Max",
                name="Mustermann",
                email="Max.Mustermann@example.com",
            )
        )
        self.db.session.commit()
        user = User.query.all()[-1]
        self.assertEqual(user.name, "Mustermann")
        self.assertEqual(user.prename, "Max")
        self.assertEqual(user.email, "Max.Mustermann@example.com")
        self.assertEqual(user.tag, b"\x00\x00\x00\x00")
        self.assertEqual(user.id, 1)
        self.assertEqual(user.tag2, None)
        self.assertEqual(user.option_oneswipe, False)
        self.assertEqual(len(user.pays), 0)
        self.assertEqual(len(user.drinks), 0)

    def test_add_user_no_tag_fails(self):
        from coffeebuddy.model import User

        self.db.session.add(
            User(
                prename="Max",
                name="Mustermann",
            )
        )
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            self.db.session.commit()

    def test_add_user_no_name_fails(self):
        from coffeebuddy.model import User

        self.db.session.add(
            User(
                tag=b"\x00\x00\x00\x00",
                prename="Max",
            )
        )
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            self.db.session.commit()

    def test_add_user_no_prename_fails(self):
        from coffeebuddy.model import User

        self.db.session.add(
            User(
                tag=b"\x00\x00\x00\x00",
                name="Mustermann",
            )
        )
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            self.db.session.commit()

    def test_add_user_not_unique_tag_fails(self):
        from coffeebuddy.model import User

        self.add_default_user()
        self.db.session.add(
            User(
                tag=b"\x01\x02\x03\x04",
                prename="Max",
                name="Mustermann",
                email="Max.Mustermann@example.com",
            )
        )
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            self.db.session.commit()

    def test_add_user_not_unique_tag2_fails(self):
        from coffeebuddy.model import User

        self.db.session.add(
            User(
                tag=b"\x00\x00\x00\x00",
                tag2=b"\x00\x00\x00\x01",
                prename="Max",
                name="Mustermann",
                email="Max.Mustermann@example.com",
            )
        )
        self.db.session.commit()
        self.db.session.add(
            User(
                tag=b"\x00\x00\x00\x01",
                tag2=b"\x00\x00\x00\x01",
                prename="Max",
                name="Mustermann",
                email="Max.Mustermann@example.com",
            )
        )
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            self.db.session.commit()

    def test_delete_user(self):
        from coffeebuddy.model import User

        self.add_default_user()
        u = User.query.first()
        self.db.session.delete(u)
        self.db.session.commit()

        self.assertEqual(len(User.query.filter(User.id == u.id).all()), 0)

    def test_user_ondelete_drinks(self):
        from coffeebuddy.model import Drink

        user1, user2 = self.add_default_user()
        user1.drinks.append(Drink(price=1))
        user1.drinks.append(Drink(price=1))
        user2.drinks.append(Drink(price=1))
        self.db.session.commit()
        self.assertEqual(len(Drink.query.all()), 3)

        self.db.session.delete(user1)
        self.db.session.commit()

        self.assertEqual(len(Drink.query.all()), 1)

    def test_user_ondelete_pays(self):
        from coffeebuddy.model import Pay

        user1, user2 = self.add_default_user()
        user1.pays.append(Pay(amount=1))
        user1.pays.append(Pay(amount=1))
        user2.pays.append(Pay(amount=1))
        self.db.session.commit()
        self.assertEqual(len(Pay.query.all()), 3)

        self.db.session.delete(user1)
        self.db.session.commit()

        self.assertEqual(len(Pay.query.all()), 1)

    def test_by_tag(self):
        from coffeebuddy.model import User

        user1, user2 = self.add_default_user()
        user1.tag2 = b"\x00\x00\x00\x00"
        self.assertEqual(User.by_tag(user1.tag), user1)
        self.assertEqual(User.by_tag(user1.tag2), user1)

    def test_by_tag_none_fails(self):
        from coffeebuddy.model import User

        user1, user2 = self.add_default_user()
        self.assertIsNone(User.by_tag(None))
        self.assertIsNone(User.by_tag(b""))


class TestModelDrink(TestCoffeebuddy):
    def test_add_drink(self):
        from coffeebuddy.model import Drink

        user1, _ = self.add_default_user()
        self.db.session.add(Drink(user=user1, price=1))
        self.db.session.commit()

        self.assertEqual(len(user1.drinks), 1)
        self.assertEqual(len(Drink.query.all()), 1)
        self.assertEqual(Drink.query.all()[0].user, user1)

    def test_add_drink_append(self):
        from coffeebuddy.model import Drink

        user1, _ = self.add_default_user()
        user1.drinks.append(Drink(price=1))
        self.db.session.commit()

        self.assertEqual(len(user1.drinks), 1)
        self.assertEqual(len(Drink.query.all()), 1)
        self.assertEqual(Drink.query.all()[0].user, user1)

    def test_add_drink_no_user_fails(self):
        from coffeebuddy.model import Drink

        self.db.session.add(Drink(price=1))
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            self.db.session.commit()

    def test_add_drink_no_price_fails(self):
        from coffeebuddy.model import Drink

        user1, _ = self.add_default_user()
        self.db.session.add(Drink(user=user1))
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            self.db.session.commit()


class TestModelPay(TestCoffeebuddy):
    def test_add_pay(self):
        from coffeebuddy.model import Pay

        user1, _ = self.add_default_user()
        self.db.session.add(Pay(user=user1, amount=1))
        self.db.session.commit()

        self.assertEqual(len(user1.pays), 1)
        self.assertEqual(len(Pay.query.all()), 1)
        self.assertEqual(Pay.query.all()[0].user, user1)

    def test_add_pay_append(self):
        from coffeebuddy.model import Pay

        user1, _ = self.add_default_user()
        user1.pays.append(Pay(amount=1))
        self.db.session.commit()

        self.assertEqual(len(user1.pays), 1)
        self.assertEqual(len(Pay.query.all()), 1)
        self.assertEqual(Pay.query.all()[0].user, user1)

    def test_add_pay_no_user_fails(self):
        from coffeebuddy.model import Pay

        self.db.session.add(Pay(amount=1))
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            self.db.session.commit()

    def test_add_drink_no_amount_fails(self):
        from coffeebuddy.model import Pay

        user1, _ = self.add_default_user()
        self.db.session.add(Pay(user=user1))
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            self.db.session.commit()
