import flask

from coffeebuddy.extensions.msteams import GraphError, TeamsClient
from coffeebuddy.model import User

blueprint = flask.Blueprint("api", __name__, template_folder="templates")


def get_user() -> User:
    user = (
        User.by_id(flask.request.args["id"])
        if "id" in flask.request.args
        else User.by_tag(bytes.fromhex(flask.request.args["tag"]))
    )
    if not user:
        return flask.abort(400)
    return user


@blueprint.route("/api/user/<string:endpoint>", methods=["GET", "POST"])
def api_user(endpoint: str):
    db = flask.current_app.db
    match endpoint:
        case "get":
            if len(flask.request.args) == 0:
                return flask.jsonify([u.serialize() for u in User.query.all()])
            user = get_user()
            return flask.jsonify(user.serialize())
        case "drinks":
            user = get_user()
            return flask.jsonify([d.serialize() for d in user.drinks])
        case "set":
            if "id" in flask.request.args:
                user: User = User.by_id(flask.request.args["id"])
                if not user:
                    return flask.abort(400)
                for key in ("email", "name", "prename", "tag", "tag2"):
                    if key in flask.request.args:
                        setattr(user, key, flask.request.args[key])
            else:
                user = User(
                    email=flask.request.args["email"],
                    name=flask.request.args["name"],
                    prename=flask.request.args["prename"],
                    tag=bytes.fromhex(flask.request.args["tag"]),
                    tag2=bytes.fromhex(flask.request.args["tag2"])
                    if "tag2" in flask.request.args
                    else None,
                )
                db.session.add(user)
            if "balance" in flask.request.args:
                user.update_balance(float(flask.request.args["balance"]))
            db.session.commit()
            return flask.jsonify(user.serialize())
        case "del":
            db.session.delete(get_user())
            db.session.commit()
            return ""
    flask.abort(404)


@blueprint.route("/api/<string:endpoint>", methods=["GET", "POST"])
def api(endpoint: str):
    if endpoint == "check_email":
        client = TeamsClient.from_config(flask.current_app.config)
        if client is None:
            return "", 404
        data = flask.request.json
        try:
            person = client.find_user(data["email"])
        except GraphError:
            return {"valid": False}
        if person is not None:
            return {
                "valid": True,
                "firstname": person.get("givenName") or "",
                "lastname": person.get("surname") or "",
            }
        return {"valid": False}
    if endpoint == "send_message":
        client = TeamsClient.from_config(flask.current_app.config)
        if client is None:
            return flask.abort(404)
        data = flask.request.json
        if "email" in data:
            client.send_markdown(data["text"], email=data["email"])
        if "chatid" in data:
            client.send_markdown(data["text"], chat_id=data["chatid"])
        return ""

    return flask.abort(404)
