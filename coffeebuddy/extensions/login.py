from dataclasses import dataclass

import flask
import flask_login


@dataclass
class AdminUser(flask_login.UserMixin):
    user_id: str

    def get_id(self):
        return self.user_id


def init():
    login_manager = flask_login.LoginManager()

    @login_manager.user_loader
    def load_user(user_id):
        return AdminUser(user_id=user_id)

    login_manager.init_app(flask.current_app)
