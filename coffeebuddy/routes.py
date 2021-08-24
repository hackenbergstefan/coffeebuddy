import datetime
import math
import subprocess

from flask import render_template, request, redirect

from coffeebuddy.model import User, Drink, Pay, db
from coffeebuddy.card import PCSCCard, MRFC522Card, PIRC522Card
from coffeebuddy import facerecognition, facerecognition_threaded, illumination, pir


def pir_motion_detected():
    subprocess.run(['xset', 'dpms', 'force', 'on'])
    illumination.color_named('pink')
    facerecognition_threaded.resume()


def pir_motion_lost():
    subprocess.run(['xset', 'dpms', 'force', 'off'])
    illumination.color_named('lightblue')
    facerecognition_threaded.pause()


def init_routes(app, socketio):
    # @app.after_request
    # def after_request(response):
    #     if app.config['FACERECOGNITION'] is True and request.endpoint:
    #         if request.endpoint == 'welcome':
    #             print(request.base_url, request.path, request.values, request.args, request.endpoint)
    #             facerecognition_threaded.resume()
    #             pir.resume()
    #         elif request.endpoint != 'static':
    #             print(request.base_url, request.path, request.values, request.args, request.endpoint)
    #             facerecognition_threaded.pause()
    #             pir.pause()
    #     return response


    # if not app.testing:
    #     if app.config['CARD'] == 'MRFC522':
    #         MRFC522Card(socketio=socketio).start()
    #     elif app.config['CARD'] == 'PCSC':
    #         PCSCCard(socketio=socketio).start()
    #     elif app.config['CARD'] == 'PIRC522':
    #         PIRC522Card(socketio=socketio).start()

    #     if app.config['FACERECOGNITION'] is True:
    #         facerecognition_threaded.start(socketio)

    #     if app.config['ILLUMINATION'] is True:
    #         illumination.setup()

    #     if app.config['PIR'] is True:
    #         pir.start(
    #             callback_on=pir_motion_detected,
    #             callback_off=pir_motion_lost,
    #         )

    import coffeebuddy.route_coffee
    coffeebuddy.route_coffee.init()

    import coffeebuddy.route_chart
    coffeebuddy.route_chart.init()

    import coffeebuddy.route_edituser
    coffeebuddy.route_edituser.init()

    import coffeebuddy.route_oneswipe
    coffeebuddy.route_oneswipe.init()

    import coffeebuddy.route_tables
    coffeebuddy.route_tables.init()

    import coffeebuddy.route_welcome
    coffeebuddy.route_welcome.init()
