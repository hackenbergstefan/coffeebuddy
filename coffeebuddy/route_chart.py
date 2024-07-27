import flask

from coffeebuddy.model import User, escapefromhex


def init():
    @flask.current_app.route("/stats.html", methods=["GET", "POST"])
    def chart():
        user = User.by_tag(escapefromhex(flask.request.args["tag"]))
        if user is None:
            return flask.render_template(
                "cardnotfound.html", uuid=flask.request.args["tag"]
            )

        if flask.request.method == "POST":
            if "coffee" in flask.request.form:
                return flask.redirect(f'coffee.html?tag={flask.request.args["tag"]}')
            return flask.redirect("/")

        return flask.render_template("stats.html", user=user)
