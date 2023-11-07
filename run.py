# -*- coding: utf-8 -*-

# Importing config data
from config import PORT, HOST

# Running the server
from app import app, socketio

socketio.run(app, host=HOST, port=PORT, debug=True)
