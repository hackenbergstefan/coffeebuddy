import logging
import threading
import time

from coffeebuddy import app


class PCSCCard(threading.Thread):
    PCSC_GET_UUID_APDU = bytes.fromhex('ff ca 00 00 00')

    def run(self):
        import smartcard
        import smartcard.CardRequest
        while True:
            try:
                request = smartcard.CardRequest.CardRequest(timeout=100, newcardonly=True)
                service = request.waitforcard()
                service.connection.connect()
                uuid = bytes(service.connection.transmit(list(self.PCSC_GET_UUID_APDU))[0])
                app.socketio.emit('card_connected', data=dict(tag=uuid.hex()))
                time.sleep(2)
                service.connection.disconnect()
            except:  # noqa: E722
                continue


class MRFC522Card(threading.Thread):
    def run(self):
        import mfrc522
        reader = mfrc522.SimpleMFRC522()
        while True:
            try:
                uuid, _ = reader.read()
                uuid = (uuid >> 8).to_bytes(4, 'big')
                app.socketio.emit('card_connected', data=dict(tag=uuid.hex()))
                time.sleep(2)
            except:  # noqa: E722
                continue


class PIRC522Card(threading.Thread):
    def run(self):
        import RPi.GPIO as GPIO
        import pirc522
        reader = pirc522.RFID(pin_rst=25, pin_irq=24, pin_mode=GPIO.BCM)
        while True:
            reader.wait_for_tag()
            for _ in range(10):
                (error, _) = reader.request()
                if not error:
                    (_, uid) = reader.anticoll()
                    logging.getLogger(__name__).info(f'Card {uid} connected.')
                    app.socketio.emit('card_connected', data=dict(tag=bytes(uid[:4]).hex()))
                    break


def init():
    if app.testing:
        return

    if app.config['CARD'] == 'MRFC522':
        MRFC522Card().start()
    elif app.config['CARD'] == 'PCSC':
        PCSCCard().start()
    elif app.config['CARD'] == 'PIRC522':
        PIRC522Card().start()
