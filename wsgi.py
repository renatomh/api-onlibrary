"""Script to run app on different plaftorms."""

import platform

from config import PORT, HOST
from app import app, socketio

if platform.system() == "Windows":
    if __name__ == "__main__":
        socketio.run(app, host=HOST, port=PORT)
if platform.system() == "Linux":
    if __name__ == "__main__":
        socketio.run(app, host=HOST, port=PORT)
