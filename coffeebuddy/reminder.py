import datetime
import logging
import random

import flask
import holidays
import pytz
import webexteamssdk

from coffeebuddy.model import User

# time bounds for reminding
time_start = datetime.time(9, 0)
time_end = datetime.time(15, 0)


def reminder_interval_from_dept(dept):
    one_week = 7
    if dept < 20:
        # never
        return datetime.timedelta(days=999999999)
    if dept < 30:
        return datetime.timedelta(days=4 * one_week)
    if dept < 40:
        return datetime.timedelta(days=3 * one_week)
    if dept < 50:
        return datetime.timedelta(days=2 * one_week)
    if dept < 80:
        return datetime.timedelta(days=one_week)
    if dept < 100:
        return datetime.timedelta(days=3)
    # above 100
    return datetime.timedelta(days=1)


def random_debt_message(x):
    return random.choice(
        [
            f"Looks like you owe the coffee fund {x}. Time to break open that piggy bank!",
            f"Hey, remember that time you drank all that coffee? Yeah, it's going to cost you {x}.",
            f"Your coffee debt is currently sitting at {x}. Don't worry, I won't send the debt collectors... yet.",
            f"I hope that coffee was worth it! You owe {x} to the coffee fund.",
            f"You owe {x} for all those cups of coffee. Looks like you'll be eating ramen for a while.",
            f"Let's just say your coffee addiction isn't doing your bank account any favors. You currently owe {x}.",
            f"I don't want to alarm you, but your coffee debt has hit {x}. Maybe it's time to switch to tea?",
            f"You're lucky you're not paying interest on your coffee debt. At least, not yet. You owe {x}.",
            f"You know what they say, a coffee a day keeps the debt collector at bay... unless you owe {x}.",
            f"I'm not saying you have a coffee problem, but you do owe {x} to the coffee fund.",
            f"You owe {x} for all the coffee you've been drinking. Maybe it's time to start bringing your own?",
            f"I hate to be the bearer of bad news, but you currently owe {x} for coffee. Time to tighten the purse strings!",
            f"Looks like you need to cut back on the coffee. Your debt has reached {x}.",
            f"You owe {x} for coffee. That's enough to buy a coffee maker and make your own!",
            f"Your coffee debt is currently sitting at {x}. Maybe it's time to switch to water?",
            f"If you're looking for a sign to quit coffee, this is it. You owe {x}.",
            f"Looks like your caffeine addiction has caught up with you. You owe {x} for coffee.",
            f"You owe {x} for coffee. Maybe it's time to start bringing your own thermos?",
            f"I hope that coffee was worth it! You owe {x} to the coffee fund.",
            f"You know what they say, a penny saved is a penny earned. You owe {x} for coffee.",
            f"Your coffee debt is currently sitting at {x}. Maybe it's time to switch to decaf?",
            f"Looks like you need to start cutting back on the caffeine. You owe {x} for coffee.",
            f"You owe {x} for coffee. Maybe it's time to start brewing your own?",
            f"Looks like your coffee addiction is getting expensive. You owe {x}.",
            f"You owe {x} for all that coffee. Maybe it's time to start bringing a flask?",
            f"Your coffee debt is currently sitting at {x}. Maybe it's time to switch to herbal tea?",
            f"I'm not saying you're addicted to coffee, but you do owe {x}.",
            f"You owe {x} for coffee. Maybe it's time to start bringing your own mug?",
            f"Looks like your coffee habit is starting to add up. You owe {x}.",
            f"You owe {x} for all that coffee. Maybe it's time to start drinking water?",
            f"Your coffee debt is currently sitting at {x}. Maybe it's time to switch to juice?",
            f"Looks like you need to start cutting back on the caffeine. You owe {x}.",
        ]
    )


def remind(app):
    with app.app_context():
        User.query.filter(User.enabled).all()

        # get timezone
        timezone_str = flask.current_app.config.get("TIMEZONE")
        timezone = pytz.timezone(timezone_str)

        # get the holidays for the specified country
        country = flask.current_app.config.get("COUNTRY")
        local_holidays = holidays.country_holidays(**country)

        api = webexteamssdk.WebexTeamsAPI(access_token=flask.current_app.config["WEBEX_ACCESS_TOKEN"])
        coffeebuddy_email = api.people.me().emails[0]

        now = datetime.datetime.now(timezone)

        # only run on work days
        if now.weekday() >= 5 or now.date() in local_holidays:
            return

        # only run when most people are at work
        if not time_start < now.time() < time_end:
            return

        # for each user, check if reminder interval is over (since last reminder)
        for user in User.query.filter(User.enabled).all():
            if not user.email:
                continue

            reminder_interval = reminder_interval_from_dept(user.unpayed)

            try:
                messages = list(api.messages.list_direct(personEmail=user.email))
            except webexteamssdk.ApiError:
                logging.getLogger(__name__).exception(f"Could not get webex messages for email={user.email}")
                continue

            reminder_messages = filter(lambda msg: msg.personEmail == coffeebuddy_email, messages)
            reminder_messages = sorted(reminder_messages, key=lambda msg: msg.created)
            try:
                last_reminder = reminder_messages[-1].created
            except StopIteration:
                # if there was no reminder yet, assume reminder ~2000 years ago (still smaller than interval 'never')
                last_reminder = datetime.datetime.min.replace(tzinfo=pytz.UTC)

            if (now - last_reminder) > reminder_interval:
                # send reminder
                message_text = random_debt_message(user.unpayed)
                try:
                    api.messages.create(toPersonEmail=user.email, text=message_text)
                except webexteamssdk.ApiError:
                    logging.getLogger(__name__).exception(f"Could not send webex message for email={user.email}")
                    continue
