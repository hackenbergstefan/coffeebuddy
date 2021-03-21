import threading
import time


class PCSCCard(threading.Thread):
    PCSC_GET_UUID = bytes.fromhex('ff ca 00 00 00')

    def __init__(self, socketio):
        super().__init__()
        self.socketio = socketio

    def run(self):
        import smartcard
        import smartcard.CardRequest
        while True:
            try:
                request = smartcard.CardRequest.CardRequest(timeout=100, newcardonly=True)
                service = request.waitforcard()
                service.connection.connect()
                uuid = bytes(service.connection.transmit(list(NFC_GET_UUID))[0])
                self.socketio.emit('card_connected', data=dict(tag=uuid.hex()))
                time.sleep(2)
                service.connection.disconnect()
            except:  # noqa: E722
                continue


class MRFC522Card(threading.Thread):
    def __init__(self, socketio):
        super().__init__()
        self.socketio = socketio

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
