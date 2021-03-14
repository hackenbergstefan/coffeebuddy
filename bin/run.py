#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import coffeetag

if __name__ == '__main__':
    app = coffeetag.create_app()
    with app.app_context():
        coffeetag.init_db(app)
    coffeetag.app.run()
