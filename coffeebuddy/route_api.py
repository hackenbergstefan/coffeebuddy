import flask

import webexteamssdk

from coffeebuddy.model import User


def init():
    @flask.current_app.route("/api/<string:endpoint>", methods=["GET", "POST"])
    def api(endpoint: str):
        if endpoint == "get_users":
            return flask.jsonify([u.serialize() for u in User.query.all()])
        if endpoint == "set_user":
            data = flask.request.json
            if "id" not in data:
                return flask.abort(400)
            user: User = User.query.filter(User.id == data["id"]).first()
            if not user:
                return flask.abort(400)

            if "email" in data:
                user.email = data["email"]
            if "name" in data:
                user.name = data["name"]
            if "prename" in data:
                user.prename = data["prename"]
            if "tag" in data:
                user.tag = bytes.fromhex(data["tag"])
            if "tag2" in data:
                user.tag2 = bytes.fromhex(data["tag2"])
            flask.current_app.db.session.commit()
            return flask.jsonify(user.serialize())
        if endpoint == "check_email":
            if not flask.current_app.config.get("WEBEX_ACCESS_TOKEN"):
                return "", 404
            api = webexteamssdk.WebexTeamsAPI(access_token=flask.current_app.config["WEBEX_ACCESS_TOKEN"])
            data = flask.request.json
            people = api.people.list(email=data["email"])
            try:
                people = list(people)
                if len(people) > 0:
                    return {"valid": True, "firstname": people[0].firstName, "lastname": people[0].lastName}
                return {"valid": False}
            except webexteamssdk.exceptions.ApiError:
                return {"valid": False}
        if endpoint == "send_message":
            if not flask.current_app.config.get("WEBEX_ACCESS_TOKEN"):
                return flask.abort(404)
            api = webexteamssdk.WebexTeamsAPI(access_token=flask.current_app.config["WEBEX_ACCESS_TOKEN"])
            data = flask.request.json
            api.messages.create(toPersonEmail=data["email"], markdown=data["text"])
            return ""

        return flask.abort(404)
