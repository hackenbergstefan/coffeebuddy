import functools

import flask

from coffeebuddy.model import CoffeeVariant, User, escapefromhex


def require_tag(func):
    """Wrapper to require a tag parameter in the request."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        request = flask.request

        user: User = User.by_tag(escapefromhex(request.args["tag"]))
        if user is None:
            return flask.render_template("cardnotfound.html", uuid=request.args["tag"])

        return func(user=user, *args, **kwargs)

    return wrapper


def require_coffeeid(func):
    """Wrapper to require a coffeeid parameter in the request."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(
            coffee=CoffeeVariant.by_id(flask.request.args["coffeeid"]), *args, **kwargs
        )

    return wrapper


def url(site: str, **kwargs):
    """Helper function to create URLs with query parameters."""
    if not kwargs:
        return site
    for key, value in kwargs.items():
        if isinstance(value, bytes):
            kwargs[key] = value.hex()
    return site + "?" + "&".join(f"{key}={value}" for key, value in kwargs.items())


@flask.current_app.context_processor
def inject_globals():
    return {
        "len": len,
        "round": round,
        "max": max,
        "min": min,
        "hexstr": lambda data: " ".join(f"{x:02x}" for x in data) if data else "",
    }


def init():
    """Initialize the UI module."""
    from . import admin, api, base, coffee, user

    app = flask.current_app
    app.register_blueprint(coffee.blueprint)
    app.register_blueprint(user.blueprint)
    app.register_blueprint(admin.blueprint)
    app.register_blueprint(base.blueprint)
    app.register_blueprint(api.blueprint)
