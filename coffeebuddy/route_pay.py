import flask

from coffeebuddy.model import Pay, User, escapefromhex


def handle_post():
    user = User.by_tag(escapefromhex(flask.request.args["tag"]))
    flask.current_app.db.session.add(Pay(user=user, amount=flask.request.form["amount"]))
    flask.current_app.db.session.commit()
    print("bla")
    return flask.redirect(f'coffee.html?tag={flask.request.args["tag"]}')
    # return flask.abort(404)


def handle_get():
    return flask.render_template(
        "pay.html",
        user=User.by_tag(escapefromhex(flask.request.args["tag"])),
    )


def init():
    @flask.current_app.route("/pay.html", methods=["GET", "POST"])
    def pay():
        if flask.request.method == "POST":
            return handle_post()
        elif flask.request.method == "GET":
            return handle_get()
        return flask.abort(404)
