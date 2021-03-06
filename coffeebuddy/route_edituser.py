import flask

from coffeebuddy.model import Pay, User, escapefromhex


def handle_post():
    try:
        userid = int(flask.request.form["id"])
    except ValueError:
        userid = None
    user = User.query.filter(User.id == userid).first()
    if user is None:
        user = User(
            tag=escapefromhex(flask.request.form["tag"]),
            tag2=escapefromhex(flask.request.form["tag2"]),
            name=flask.request.form["last_name"],
            prename=flask.request.form["first_name"],
            option_oneswipe="oneswipe" in flask.request.form,
        )
        flask.current_app.db.session.add(user)
        flask.current_app.db.session.commit()
    else:
        # Edit existing new user
        user.tag = escapefromhex(flask.request.form["tag"])
        user.tag2 = escapefromhex(flask.request.form["tag2"])
        user.name = flask.request.form["last_name"]
        user.prename = flask.request.form["first_name"]
        user.option_oneswipe = "oneswipe" in flask.request.form
    try:
        bill = float(flask.request.form["initial_bill"].replace(",", "."))
        if bill != user.unpayed:
            flask.current_app.db.session.add(Pay(user=user, amount=user.unpayed - bill))
    except ValueError:
        pass
    flask.current_app.db.session.commit()
    return flask.redirect("/")


def handle_get():
    tag = escapefromhex(flask.request.args["tag"])
    return flask.render_template(
        "edituser.html",
        user=User.by_tag(tag) or User(tag=tag, name="", prename=""),
    )


def init():
    @flask.current_app.route("/edituser.html", methods=["GET", "POST"])
    def edit_user():
        if flask.request.method == "POST":
            return handle_post()
        elif flask.request.method == "GET":
            return handle_get()
        return flask.abort(404)
