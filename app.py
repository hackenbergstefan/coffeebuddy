from flask import Flask, url_for, render_template, request

app = Flask(__name__)


import database
database.init_db()

from user import User

@app.route('/coffee.html', methods=['GET', 'POST'])
def hello():
    user = User.query.filter(User.tag == request.args['tag'].encode()).first()
    if request.method == 'POST' and 'coffee' in request.form:
        user.coffees += 1
        database.db_session.commit()
    return render_template('coffee.html', user=user)


@app.teardown_appcontext
def shutdown_session(exception=None):
    from database import db_session
    db_session.remove()
