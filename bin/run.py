#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import coffeetag

if __name__ == '__main__':
    coffeetag.create_app()
    coffeetag.app.run()