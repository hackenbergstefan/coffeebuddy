import datetime

from . import TestCoffeebuddy


class TestDatabase(TestCoffeebuddy):
    def test_drink_coffee(self):
        from coffeebuddy.model import User

        user1 = User(tag=b'\x01\x02\x03', name='Mustermann', prename='Max')
        user2 = User(tag=b'\x03\x04\x05', name='Doe', prename='Jane')
        self.db.session.add(user1)
        self.db.session.add(user2)
        self.db.session.commit()
        response = self.client.post('/coffee.html?tag=010203', data=dict(coffee='coffee'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(user1.coffees), 1)
        self.assertEqual(len(user1.coffees_today), 1)
        response = self.client.post('/coffee.html?tag=030405', data=dict(coffee='coffee'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(user2.coffees), 1)

    def test_drinks_today(self):
        from coffeebuddy.model import Drink, User

        user1 = User(tag=b'\x01\x02\x03', name='Mustermann', prename='Max')
        user2 = User(tag=b'\x03\x04\x05', name='Doe', prename='Jane')
        self.db.session.add(user1)
        self.db.session.add(user2)
        self.db.session.commit()

        user1.coffees.append(Drink(price=30))
        user1.coffees.append(Drink(price=30, timestamp=datetime.datetime.now() - datetime.timedelta(days=1)))
        user2.coffees.append(Drink(price=30))

        self.assertEqual(len(user1.coffees), 2)
        self.assertEqual(len(user1.coffees_today), 1)
        self.assertEqual(len(user2.coffees), 1)

    def test_pay(self):
        from coffeebuddy.model import Drink, User, Pay

        user = User(tag=b'\x01\x02\x03', name='Mustermann', prename='Max')
        self.db.session.add(user)
        self.db.session.commit()

        user.coffees.append(Drink(price=30))
        user.coffees.append(Drink(price=30))
        user.coffees.append(Drink(price=30))
        user.pays.append(Pay(amount=60))
        self.db.session.commit()

        self.assertEqual(user.unpayed, 30)


class TestRouteEdituser(TestCoffeebuddy):
    def test_adduser(self):
        from coffeebuddy.model import User

        response = self.client.post(
            '/edituser.html',
            data=dict(
                tag='01 02 03 04',
                last_name='Mustermann',
                first_name='Max',
                initial_bill=0,
            ),
        )
        self.assertEqual(response.status_code, 302)
        users = User.query.all()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].tag, b'\x01\x02\x03\x04')
        self.assertEqual(users[0].name, 'Mustermann')
        self.assertEqual(users[0].prename, 'Max')

    def test_edituser(self):
        from coffeebuddy.model import User

        self.db.session.add(User(tag=b'\x01\x02\x03\x04', name='Mustermann', prename='Max'))
        response = self.client.post(
            '/edituser.html?tag=01020304',
            data=dict(
                tag='01 02 03 04',
                last_name='Doe',
                first_name='Jane',
            ),
        )
        self.assertEqual(response.status_code, 302)
        users = User.query.all()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].tag, b'\x01\x02\x03\x04')
        self.assertEqual(users[0].name, 'Doe')
        self.assertEqual(users[0].prename, 'Jane')


class TestRouteCoffee(TestCoffeebuddy):
    def test_non_existing_user(self):
        response = self.client.get('/coffee.html?tag=00', follow_redirects=True)
        self.assertIn(b'Card not found', response.data)

    def test_existing_user(self):
        self.add_default_user()
        response = self.client.get('/coffee.html?tag=010203')
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        self.add_default_user()
        response = self.client.post('/coffee.html?tag=010203', data=dict(logout=''))
        self.assertEqual(response.status_code, 302)

    def test_undopay(self):
        from coffeebuddy.model import Pay

        user, _ = self.add_default_user()
        user.pays.append(Pay(amount=10))
        response = self.client.post('/coffee.html?tag=010203', data=dict(undopay=''))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(user.pays), 0)

    def test_undopay_empty(self):
        user, _ = self.add_default_user()
        response = self.client.post('/coffee.html?tag=010203', data=dict(undopay=''))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(user.pays), 0)


class TestRouteOneSwipe(TestCoffeebuddy):
    def test(self):
        user, _ = self.add_default_user()
        response = self.client.post(f'/oneswipe.html?tag={user.tag.hex()}', data=dict(coffee=True))
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(list(user.drinks())), 0)


class TestRouteWelcome(TestCoffeebuddy):
    def test(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
