from flask import Flask, url_for, render_template, request, abort

app = Flask(__name__)


import coffeetag.database
coffeetag.database.init_db()

from coffeetag.user import User

@app.route('/coffee.html', methods=['GET', 'POST'])
def hello():
    user = User.query.filter(User.tag == request.args['tag'].encode()).first()
    if user is None:
        return abort(404)
    if request.method == 'POST' and 'coffee' in request.form:
        user.coffees += 1
        coffeetag.database.db_session.commit()
    return render_template('coffee.html', user=user)


@app.teardown_appcontext
def shutdown_session(exception=None):
    coffeetag.database.db_session.remove()
