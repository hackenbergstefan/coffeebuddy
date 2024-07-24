import itertools

import flask

from coffeebuddy.model import User


def init():
    @flask.current_app.route("/selectuser.html")
    def selectuser():
        all_enabled_users = User.query.filter(User.enabled).order_by(User.name).all()
        return flask.render_template(
            "selectuser.html",
            users=itertools.groupby(all_enabled_users, key=lambda u: u.name[0].upper()),
            top_manual_users=list(
                sorted(
                    (u for u in all_enabled_users if u.count_selected_manually() > 0),
                    key=lambda u: u.count_selected_manually(),
                    reverse=True,
                )
            )[:5],
        )
