#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import coffeebuddy  # noqa: E402

if __name__ == '__main__':
    app, socketio = coffeebuddy.create_app()
    with app.app_context():
        coffeebuddy.init_db(app)
    socketio.run(app, host="0.0.0.0")
