"""Main script to run the application."""

from config import PORT, HOST
from app import app, socketio

socketio.run(app, host=HOST, port=PORT, debug=True)
