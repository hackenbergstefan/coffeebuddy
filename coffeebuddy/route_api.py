import flask

import webexteamssdk

from coffeebuddy.model import User


def init():
    @flask.current_app.route("/api/<string:endpoint>", methods=["POST"])
    def api(endpoint: str):
        if endpoint == "get_users":
            return flask.jsonify(list(map(User.serialize, User.query.all())))
        elif endpoint == "set_user":
            data = flask.request.json
            if "id" not in data:
                flask.abort(400)
            user: User = User.query.filter(User.id == data["id"]).first()
            if not user:
                flask.abort(400)

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
        elif endpoint == "check_email":
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
        elif endpoint == "send_message":
            if not flask.current_app.config.get("WEBEX_ACCESS_TOKEN"):
                return "", 404
            api = webexteamssdk.WebexTeamsAPI(access_token=flask.current_app.config["WEBEX_ACCESS_TOKEN"])
            data = flask.request.json
            api.messages.create(toPersonEmail=data["email"], markdown=data["text"])
        else:
            flask.abort(404)
