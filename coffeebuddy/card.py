import logging
import threading
import time

import flask


class PCSCCard(threading.Thread):
    PCSC_GET_UUID_APDU = bytes.fromhex('ff ca 00 00 00')

    def __init__(self):
        super().__init__()
        self.socketio = flask.current_app.socketio

    def run(self):
        import smartcard
        import smartcard.CardRequest

        while True:
            try:
                request = smartcard.CardRequest.CardRequest(timeout=100, newcardonly=True)
                service = request.waitforcard()
                service.connection.connect()
                uuid = bytes(service.connection.transmit(list(self.PCSC_GET_UUID_APDU))[0])
                self.socketio.emit('card_connected', data=dict(tag=uuid.hex()))
                time.sleep(2)
                service.connection.disconnect()
            except:  # noqa: E722
                continue


class MRFC522Card(threading.Thread):
    def __init__(self):
        super().__init__()
        self.socketio = flask.current_app.socketio

    def run(self):
        import mfrc522

        reader = mfrc522.SimpleMFRC522()
        while True:
            try:
                uuid, _ = reader.read()
                uuid = (uuid >> 8).to_bytes(4, 'big')
                self.socketio.emit('card_connected', data=dict(tag=uuid.hex()))
                time.sleep(2)
            except:  # noqa: E722
                continue


class PIRC522Card(threading.Thread):
    def __init__(self):
        super().__init__()
        self.socketio = flask.current_app.socketio

    def run(self):
        import RPi.GPIO as GPIO
        import pirc522

        pirc522.RFID.antenna_gain = 0x07
        reader = pirc522.RFID(pin_rst=25, pin_irq=24, pin_mode=GPIO.BCM)
        while True:
            reader.wait_for_tag()
            for _ in range(10):
                (error, _) = reader.request()
                if not error:
                    (_, uid) = reader.anticoll()
                    logging.getLogger(__name__).info(f'Card {uid} connected.')
                    self.socketio.emit('card_connected', data=dict(tag=bytes(uid[:4]).hex()))
                    break


def init():
    if flask.current_app.testing:
        return

    if flask.current_app.config['CARD'] == 'MRFC522':
        MRFC522Card().start()
    elif flask.current_app.config['CARD'] == 'PCSC':
        PCSCCard().start()
    elif flask.current_app.config['CARD'] == 'PIRC522':
        PIRC522Card().start()
