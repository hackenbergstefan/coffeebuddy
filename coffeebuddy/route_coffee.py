import flask
from flask import request, render_template, redirect

from coffeebuddy.model import Drink, User, Pay


def init():
    @flask.g.app.route('/coffee.html', methods=['GET', 'POST'])
    def coffee():
        # illumination.color_named('green')
        user = User.query.filter(User.tag == bytes.fromhex(request.args['tag'])).first()
        if user is None:
            return render_template('cardnotfound.html', uuid=request.args['tag'])
        if request.method == 'GET' and user.option_oneswipe:
            return render_template('oneswipe.html', user=user)
        if request.method == 'POST':
            if 'coffee' in request.form:
                flask.g.db.session.add(Drink(user=user, price=flask.g.app.config['PRICE']))
                flask.g.db.session.commit()
            elif 'pay' in request.form:
                flask.g.db.session.add(Pay(user=user, amount=request.form['pay']))
                flask.g.db.session.commit()
            elif 'undopay' in request.form:
                # TODO: Really deleting pay? Introduce property 'undone' on Pay?
                if len(user.pays) > 0:
                    flask.g.db.session.delete(user.pays[-1])
                    flask.g.db.session.commit()
            elif 'logout' in request.form:
                return redirect('/')
            elif 'edituser' in request.form:
                return redirect(f'edituser.html?tag={request.args["tag"]}')
            elif 'stats' in request.form:
                return redirect(f'stats.html?tag={request.args["tag"]}')
            elif 'capture' in request.form:
                # if 'notimeout' in request.args:
                    # if app.config['FACERECOGNITION'] is True:
                    #     facerecognition_threaded.pause()
                    #     facerecognition.FaceCapturer(user.tag, user.name, user.prename).capture()
                return redirect(f'{request.url}&notimeout')

        return render_template(
            'coffee.html',
            user=user,
            referer=request.form if request.method == 'POST' else [],
        )
