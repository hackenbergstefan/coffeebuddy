import flask
import flask_login

from coffeebuddy import AdminUser


def init():
    @flask.current_app.route("/login.html", methods=["GET", "POST"])
    def login():
        if not flask.current_app.config.get("ADMIN_PASSWORD"):
            return flask.abort(404)
        if flask.request.method == "POST":
            password = flask.request.form.get("password")
            if password == flask.current_app.config["ADMIN_PASSWORD"]:
                flask_login.login_user(AdminUser(user_id="admin"), remember=True)
                return flask.redirect("/tables.html")
        return flask.render_template("login.html")
