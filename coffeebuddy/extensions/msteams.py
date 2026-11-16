"""
This extension handles Microsoft Teams messages via Microsoft Graph.

Microsoft Graph only allows sending chat messages with delegated permissions, so
Coffeebuddy acts on behalf of a dedicated Microsoft 365 account. It signs in with
the account's username and password (resource owner password credentials flow)
using a confidential Entra ID app (client id + secret).
"""

import datetime
import functools
import itertools
import logging
import random
import re
import subprocess
import threading
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import Iterable, Iterator
from urllib.parse import parse_qs, unquote, urlparse

import flask
import holidays
import markdown
import msal
import pytz
import requests
from apscheduler.schedulers.background import BackgroundScheduler

from coffeebuddy.model import Pay, User

GRAPH_URL = "https://graph.microsoft.com/v1.0"
# All delegated permissions consented for the app registration
SCOPES = ["https://graph.microsoft.com/.default"]

# Number of latest chat messages searched for the last payment notification
PAYMENT_NOTIFICATION_LOOKBACK = 200

_token_lock = threading.Lock()


class GraphError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


@functools.lru_cache
def _msal_app(
    client_id: str, client_secret: str, tenant_id: str
) -> msal.ConfidentialClientApplication:
    # Cached to share the in-memory token cache between all TeamsClient instances
    return msal.ConfidentialClientApplication(
        client_id,
        client_credential=client_secret,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
    )


class TeamsClient:
    """Minimal synchronous Microsoft Graph client for Teams chats."""

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
    ):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.session = requests.Session()
        self._me = None
        self._direct_chat_ids: dict[str, str] = {}

    @classmethod
    def from_config(cls, config) -> "TeamsClient | None":
        keys = ("TENANT_ID", "CLIENT_ID", "CLIENT_SECRET", "USERNAME", "PASSWORD")
        values = [config.get(f"MSTEAMS_{key}") for key in keys]
        if not all(values):
            return None
        return cls(*values)

    def access_token(self) -> str:
        with _token_lock:
            try:
                app = _msal_app(self.client_id, self.client_secret, self.tenant_id)
                accounts = app.get_accounts(username=self.username)
                result = (
                    app.acquire_token_silent(SCOPES, account=accounts[0])
                    if accounts
                    else None
                )
                if not result or "access_token" not in result:
                    result = app.acquire_token_by_username_password(
                        self.username, self.password, scopes=SCOPES
                    )
            except (ValueError, requests.RequestException) as error:
                raise GraphError(f"Could not acquire Microsoft token: {error}")
            if "access_token" not in result:
                raise GraphError(
                    "Microsoft login failed: "
                    f"{result.get('error')}: {result.get('error_description')}"
                )
            return result["access_token"]

    def request(self, method: str, url: str, **kwargs) -> dict | None:
        if not url.startswith("https://"):
            url = GRAPH_URL + url
        headers = {"Authorization": f"Bearer {self.access_token()}"}
        headers.update(kwargs.pop("headers", {}))
        try:
            response = self.session.request(
                method, url, headers=headers, timeout=60, **kwargs
            )
        except requests.RequestException as error:
            raise GraphError(f"{method} {url} failed: {error}")
        if not response.ok:
            raise GraphError(
                f"{method} {url} failed ({response.status_code}): {response.text}",
                status_code=response.status_code,
            )
        return response.json() if response.content else None

    def paginate(self, url: str, params: dict | None = None) -> Iterator[dict]:
        while url:
            data = self.request("GET", url, params=params)
            yield from data.get("value", [])
            # nextLink already contains all query parameters
            url, params = data.get("@odata.nextLink"), None

    def me(self) -> dict:
        if self._me is None:
            self._me = self.request(
                "GET", "/me", params={"$select": "id,mail,userPrincipalName"}
            )
        return self._me

    def find_user(self, email: str) -> dict | None:
        """Find an Entra ID user by email address or user principal name."""
        email = email.replace("'", "''")
        users = self.request(
            "GET",
            "/users",
            params={
                "$filter": f"mail eq '{email}' or userPrincipalName eq '{email}'",
                "$select": "id,givenName,surname,mail,userPrincipalName",
            },
        )["value"]
        return users[0] if users else None

    def direct_chats(self) -> dict[str, str]:
        """Return a mapping of `email (lowercase) -> chat id` of existing 1:1 chats."""
        me_id = self.me()["id"]
        chats = {}
        for chat in self.paginate("/me/chats", params={"$expand": "members"}):
            if chat.get("chatType") != "oneOnOne":
                continue
            for member in chat.get("members", []):
                if member.get("userId") != me_id and member.get("email"):
                    chats[member["email"].lower()] = chat["id"]
        self._direct_chat_ids.update(chats)
        return chats

    def direct_chat_id(self, email: str) -> str:
        """Return the id of the 1:1 chat with `email`. Creates the chat if necessary."""
        key = email.lower()
        if key not in self._direct_chat_ids:
            user = self.find_user(email)
            if user is None:
                raise GraphError(f"No Microsoft Teams user found for {email}", 404)
            chat = self.request(
                "POST",
                "/chats",
                json={
                    "chatType": "oneOnOne",
                    "members": [
                        {
                            "@odata.type": "#microsoft.graph.aadUserConversationMember",
                            "roles": ["owner"],
                            "user@odata.bind": f"{GRAPH_URL}/users('{uid}')",
                        }
                        for uid in (self.me()["id"], user["id"])
                    ],
                },
            )
            self._direct_chat_ids[key] = chat["id"]
        return self._direct_chat_ids[key]

    def messages(self, chat_id: str) -> Iterator[dict]:
        """Iterate over the messages of a chat, newest first."""
        return self.paginate(
            f"/chats/{chat_id}/messages",
            params={"$top": 50, "$orderby": "createdDateTime desc"},
        )

    def channel_messages(self, team_id: str, channel_id: str) -> Iterator[dict]:
        """Iterate over the (root) messages of a team channel, newest first."""
        return self.paginate(
            f"/teams/{team_id}/channels/{channel_id}/messages",
            params={"$top": 50},
        )

    def is_own_message(self, message: dict) -> bool:
        sender = (message.get("from") or {}).get("user") or {}
        return (
            message.get("messageType") == "message"
            and sender.get("id") == self.me()["id"]
        )

    def _post_message(
        self, url: str, html: str, attachments: list[dict] | None = None
    ) -> dict:
        body = {"body": {"contentType": "html", "content": html}}
        if attachments:
            body["attachments"] = attachments
        return self.request("POST", url, json=body)

    def send(self, chat_id: str, html: str) -> dict:
        return self._post_message(f"/chats/{chat_id}/messages", html)

    def send_channel(
        self,
        team_id: str,
        channel_id: str,
        html: str,
        attachments: list[dict] | None = None,
    ) -> dict:
        return self._post_message(
            f"/teams/{team_id}/channels/{channel_id}/messages", html, attachments
        )

    def send_markdown(
        self,
        text: str,
        email: str | None = None,
        chat_id: str | None = None,
    ) -> dict:
        """Send a markdown message either to a person (by email) or to a chat."""
        if email is not None:
            chat_id = self.direct_chat_id(email)
        return self.send(chat_id, markdown_to_html(text))

    def send_channel_markdown(self, text: str, team_id: str, channel_id: str) -> dict:
        """Send a markdown message to a team channel."""
        return self.send_channel(team_id, channel_id, markdown_to_html(text))

    def send_channel_file(self, team_id: str, channel_id: str, path: Path) -> dict:
        """Upload `path` to the files folder of a team channel and post it there."""
        folder = self.request(
            "GET", f"/teams/{team_id}/channels/{channel_id}/filesFolder"
        )
        item = self.request(
            "PUT",
            f"/drives/{folder['parentReference']['driveId']}/items/{folder['id']}"
            f":/{path.name}:/content",
            data=path.read_bytes(),
            headers={"Content-Type": "application/octet-stream"},
        )
        attachment_id = attachment_id_from_etag(item["eTag"])
        return self.send_channel(
            team_id,
            channel_id,
            f'<attachment id="{attachment_id}"></attachment>',
            attachments=[
                {
                    "id": attachment_id,
                    "contentType": "reference",
                    "contentUrl": item["webUrl"],
                    "name": item["name"],
                }
            ],
        )


def markdown_to_html(text: str) -> str:
    return markdown.markdown(text)


def attachment_id_from_etag(etag: str) -> str:
    """Extract the GUID from a driveItem eTag like `"{GUID},1"`."""
    match = re.search(r"\{([0-9A-Fa-f-]+)\}", etag)
    if match is None:
        raise GraphError(f"Unexpected driveItem eTag: {etag}")
    return match.group(1)


def parse_channel_link(link: str) -> tuple[str, str]:
    """
    Return `(team_id, channel_id)` from a Teams channel link like
    `https://teams.microsoft.com/l/channel/<channel_id>/<name>?groupId=<team_id>&...`.
    """
    url = urlparse(link)
    parts = url.path.split("/")
    team_ids = parse_qs(url.query).get("groupId")
    if len(parts) < 4 or parts[1:3] != ["l", "channel"] or not team_ids:
        raise ValueError(f"Not a Teams channel link: {link}")
    return team_ids[0], unquote(parts[3])


def last_notified_pay_id(client: TeamsClient, messages: Iterable[dict]) -> int:
    """Return the highest `pay.id` of the payment notifications in `messages`."""
    pay_ids = [-1]
    for message in itertools.islice(messages, PAYMENT_NOTIFICATION_LOOKBACK):
        if not client.is_own_message(message):
            continue
        match = re.search(
            r"pay\.id:(?:\s|&nbsp;|<[^>]*>)*(\d+)",
            message["body"].get("content") or "",
        )
        if match is not None:
            pay_ids.append(int(match.group(1)))
    return max(pay_ids)


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


def random_debt_message(dept):
    x = f"{dept:.2f}€"
    return random.choice(
        # ruff: noqa: E501
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


def remind(app: flask.Flask):
    """
    Remind users about their dept via Microsoft Teams.
    """
    # pylint: disable=too-many-locals
    with app.app_context():
        # get timezone
        timezone_str = app.config.get("TIMEZONE")
        timezone = pytz.timezone(timezone_str)

        # get the holidays for the specified country
        country = app.config.get("COUNTRY")
        local_holidays = holidays.country_holidays(**country)

        now = datetime.datetime.now(timezone)

        # only run on work days
        if now.weekday() >= 5 or now.date() in local_holidays:
            return

        # only run when most people are at work
        if not time_start < now.time() < time_end:
            return

        client = TeamsClient.from_config(app.config)
        direct_chats = client.direct_chats()

        # for each user, check if reminder interval is over (since last reminder)
        for user in User.query.filter(User.enabled).all():
            if not user.email:
                continue

            reminder_interval = reminder_interval_from_dept(user.unpayed)
            # if there was no reminder yet, assume reminder ~2000 years ago (still smaller than interval 'never')
            last_reminder = datetime.datetime.min.replace(tzinfo=pytz.UTC)

            # get date of last reminder (= latest message by coffeebuddy)
            chat_id = direct_chats.get(user.email.lower())
            if chat_id is not None:
                try:
                    last_reminder = next(
                        (
                            datetime.datetime.fromisoformat(msg["createdDateTime"])
                            for msg in client.messages(chat_id)
                            if client.is_own_message(msg)
                        ),
                        last_reminder,
                    )
                except GraphError:
                    logging.getLogger(__name__).exception(
                        f"Could not get Teams messages for email={user.email}"
                    )
                    continue

            # if it's time, send reminder
            if (now - last_reminder) > reminder_interval:
                message_oneliner = random_debt_message(user.unpayed)
                message_md = app.config.get("REMINDER_MESSAGE").format(
                    oneliner=message_oneliner
                )
                try:
                    client.send_markdown(message_md, email=user.email)
                except GraphError:
                    logging.getLogger(__name__).exception(
                        f"Could not send Teams message for email={user.email}"
                    )
                    continue


def notify_payment(app: flask.Flask, channels: list[tuple[str, str]]) -> None:
    """Post today's payments to the Teams channels `[(team_id, channel_id), ...]`."""
    with app.app_context():
        pays = Pay.todays()
        if not pays:
            return

        client = TeamsClient.from_config(app.config)
        last_notified_id = last_notified_pay_id(
            client, client.channel_messages(*channels[0])
        )

        for pay in pays:
            if pay.id <= last_notified_id:
                continue
            message = dedent(
                f"""\
                ### 💰 {pay.user.name} {pay.user.prename} payed {pay.amount:.2f}€

                Their balance was: **{pay.user.balance - pay.amount:.2f}€**.
                Their balance now: **{pay.user.balance:.2f}€**.

                ##### Details
                - User: {pay.user} (id: `{pay.user.id}`)
                - Timestamp: {pay.timestamp}

                _Your Coffeebuddy_ (pay.id: `{pay.id}`)
                """
            )
            for team_id, channel_id in channels:
                try:
                    client.send_channel_markdown(message, team_id, channel_id)
                except GraphError:
                    logging.getLogger(__name__).exception(
                        f"Could not send Teams message to channel={channel_id}"
                    )


def disable_deleted_accounts(app: flask.Flask, channel: tuple[str, str]) -> None:
    """Disable accounts that have been deleted in Microsoft Entra ID."""
    with app.app_context():
        client = TeamsClient.from_config(app.config)
        for user in User.query.filter(User.enabled).all():
            if not user.email:
                continue
            try:
                if client.find_user(user.email) is None:
                    user.enabled = False
                    app.db.session.commit()
                    client.send_channel_markdown(
                        f"## Disabled: {user} ({user.id})", *channel
                    )
            except GraphError:
                # Maybe error in email address
                pass


def init():
    app = flask.current_app
    if app.testing:
        return

    client = TeamsClient.from_config(app.config)
    if client is None:
        return

    try:
        client.access_token()
    except GraphError as error:
        logging.getLogger(__name__).warning(str(error))

    reminders = app.config.get("REMINDER_MESSAGE")
    backup_link = app.config.get("MSTEAMS_DATABASE_BACKUP")
    backup_channel = parse_channel_link(backup_link) if backup_link else None
    payment_notification_channels = [
        parse_channel_link(link)
        for link in app.config.get("PAYMENT_NOTIFICATION_CHANNELS") or []
    ]

    scheduler = BackgroundScheduler()
    scheduler.start()

    if reminders:
        scheduler.add_job(
            func=remind,
            args=(app._get_current_object(),),
            trigger="interval",
            minutes=60,
            id="msteams dept reminder",
            name="msteams dept reminder",
            replace_existing=True,
        )

    if payment_notification_channels:
        scheduler.add_job(
            func=notify_payment,
            args=(app._get_current_object(), payment_notification_channels),
            trigger="interval",
            minutes=1,
            id="msteams payment notification",
            name="msteams payment notification",
            replace_existing=True,
        )

    if backup_channel:
        app = app._get_current_object()

        @scheduler.scheduled_job("cron", day_of_week="sun")
        def backup_database():
            with TemporaryDirectory() as tmpdir, app.app_context():
                backupfile = Path(tmpdir) / "coffeebuddydb-backup-{}".format(
                    datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S.sql")
                )
                backupfile.write_text(
                    subprocess.check_output(
                        [
                            "sudo",
                            "docker-compose",
                            "exec",
                            "coffeebuddydb",
                            "pg_dump",
                            "-U",
                            "coffeebuddydb",
                            "-d",
                            "coffeebuddy",
                        ],
                        cwd="database",
                        universal_newlines=True,
                    )
                )

                TeamsClient.from_config(app.config).send_channel_file(
                    *backup_channel, backupfile
                )

        scheduler.scheduled_job("cron", day_of_week="sat", args=(app, backup_channel))(
            disable_deleted_accounts
        )
