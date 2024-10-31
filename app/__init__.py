"""Main Flask applcation."""

import os
import re
import time

from flask import Flask, jsonify, send_from_directory, redirect
from flask.globals import request
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_babel import Babel, _
from flask_socketio import SocketIO, emit
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from flasgger import Swagger
from werkzeug.utils import secure_filename
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import SQLALCHEMY_DATABASE_URI, DATABASE_CONNECT_OPTIONS

# Initialize Sentry
try:
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN", None),
        integrations=[FlaskIntegration()],
        # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
    )
# If something goes wrong, we just ignore and log the error
except Exception as e:
    print("It was not possible to setup Sentry, hence it won't be used", e)

app = Flask(__name__)


@app.route("/debug-sentry")
def trigger_error():
    """This route is only used to trigger an error and check if Sentry is working properly."""
    1 / 0


# Initialize Flasgger
Swagger(
    app,
    template={
        "swagger": "2.0",
        "info": {
            "title": "API Documentation",
            "description": "API for Web Application",
            "version": "0.1",
        },
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "Add your JWT token with 'Bearer' prefix",
            }
        },
    },
)

app.config.from_object("config")

# Database object imported by modules and controllers
db = SQLAlchemy(app)

# We must wait for the app to be fully initialized to import middlewares, to avoid circular imports
from app.middleware import ensure_authorized

# Setting up limiter to avoid DOS attacks (https://flask-limiter.readthedocs.io/en/stable/)
limiter = Limiter(app, key_func=get_remote_address, default_limits=["10/second"])

# Allowing access through sites (such as when using ReactJS)
CORS(app)

# Adding internationalization and location to app
babel = Babel(app)


@babel.localeselector
def get_locale():
    """Selects language according to Accept-Language header from the incoming request."""
    return request.accept_languages.best_match(app.config["LANGUAGES"].keys())


# Creating the Socket.IO server
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")


@socketio.on("connect")
def connected():
    """Event listener when client connects to the server."""
    print(f"New client has connected (SID: {request.sid})")


@socketio.on("event")
def handle_message(data):
    """Event listener for when client sends generic data via 'event'."""
    print(f"Data from client (SID: {request.sid}):", str(data))
    # emit("event", {'data': data, 'id': request.sid}, broadcast=True)


@socketio.on("disconnect")
def disconnected():
    """Event listener when client disconnects from the server."""
    print(f"Client has disconnected (SID: {request.sid})")


@app.route("/")
def index():
    """On the root endpoint, we'll redirect to the Swagger API documentation."""
    return redirect("apidocs", 302)


@app.route("/files/<path:path>")
def files(path):
    """Setting up static files serving."""
    return send_from_directory(os.path.join(app.config["UPLOAD_FOLDER"]), path)


@app.route("/send-socketio-message", methods=["POST"])
@ensure_authorized
def send_socketio_message():
    """Sample Socket.IO messages sending route."""

    data = request.json

    # Creating a list with possible errors to be returned to the client
    error_messages = []
    # Checking if the event name was provided
    if "event" not in data.keys() or not data["event"]:
        error_messages.append(_("You must provide the 'event' name."))
    # Checking if the broadcast flag was provided
    if "should_broadcast" not in data.keys() or data["should_broadcast"] not in [
        True,
        False,
    ]:
        error_messages.append(
            _(
                "You must inform if message should be broadcast "
                "('should_broadcast' flag as 'true' or 'false')."
            )
        )
    # When not broadcasting, the session ID must be informed
    if (
        "should_broadcast" in data.keys()
        and not data["should_broadcast"]
        and ("sid" not in data.keys() or not data["sid"])
    ):
        error_messages.append(
            _("You must inform the session ID ('sid') when not broadcasting.")
        )
    # Checking if the message content was provided
    if "message" not in data.keys() or not data["message"]:
        error_messages.append(
            _("You must provide the message content as 'json' to be sent.")
        )
    # If there were errors on the request
    if len(error_messages) > 0:
        return (
            jsonify({"data": [], "meta": {"success": False, "errors": error_messages}}),
            400,
        )

    # If everything is ok, we emit the message (either broadcast or to specific client)
    if data["should_broadcast"]:
        socketio.emit(data["event"], data["message"], broadcast=True)
    else:
        socketio.emit(data["event"], data["message"], to=data["sid"])

    return jsonify(
        {
            "data": {"message": _("Message sent successfully")},
            "meta": {"success": True},
        }
    )


# Import services
from app.services.storage import store_file
from app.services.push_notification import send_message, send_multicast_message


@app.route("/files/upload", methods=["POST"])
@ensure_authorized
def upload_file():
    """Files upload route."""

    print(request.files)
    file = request.files["file"]

    # Setting filename with timestamp to create almost unique filename
    filename = f"{round(time.time()*1000)}-{secure_filename(file.filename)}"

    # Checking if file extension is allowed
    if (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_FILE_EXTENSIONS"]
    ):
        # Loading to the temp folder
        file.save(os.path.join(app.config["UPLOAD_TEMP_FOLDER"], filename))

        # Calling the function to upload file to selected directory/container
        upload_response = store_file(
            os.path.join(app.config["UPLOAD_TEMP_FOLDER"], filename), filename
        )

        # Returning the upload response
        return jsonify(upload_response)

    return (
        jsonify(
            {
                "data": {},
                "meta": {
                    "success": False,
                    "errors": f"File extenstion not allowed {app.config['ALLOWED_FILE_EXTENSIONS']}",
                },
            }
        ),
        400,
    )


@app.route("/send-push-notification-message", methods=["POST"])
@ensure_authorized
def send_push_notification_message():
    """Sample push notification message sending route function."""

    # Getting request data as a dict
    data = request.json

    # Creating a list with possible errors to be returned to the client
    error_messages = []
    # Checking if the notification title was provided
    if "title" not in data.keys() or not data["title"]:
        error_messages.append(_("You must provide the notification 'title'."))
    # Checking if the notification body was provided
    if "body" not in data.keys() or not data["body"]:
        error_messages.append(_("You must provide the notification 'body'."))
    # Checking if the multicast flag was provided
    if "should_multicast" not in data.keys() or data["should_multicast"] not in [
        True,
        False,
    ]:
        error_messages.append(
            _(
                "You must inform if message should be multicast "
                "('should_multicast' flag as 'true' or 'false')."
            )
        )
    # When not multicasting, one token must be provided
    if (
        "should_multicast" in data.keys()
        and not data["should_multicast"]
        and (
            "token" not in data.keys()
            or not data["token"]
            or type(data["token"]) != str
        )
    ):
        error_messages.append(
            _("You must inform one token ('token') when not multicasting.")
        )
    # When multicasting, a list of tokens must be provided
    if (
        "should_multicast" in data.keys()
        and data["should_multicast"]
        and (
            "tokens" not in data.keys()
            or not data["tokens"]
            or type(data["tokens"]) != list
        )
    ):
        error_messages.append(
            _("You must inform a list of tokens ('tokens') when multicasting.")
        )
    # If there were errors on the request
    if len(error_messages) > 0:
        return (
            jsonify({"data": [], "meta": {"success": False, "errors": error_messages}}),
            400,
        )

    # If everything is ok, we send the push notification message (either multicast or to specific client)
    try:
        if data["should_multicast"]:
            send_multicast_message(data["tokens"], data["title"], data["body"])
        else:
            send_message(data["token"], data["title"], data["body"])

        return jsonify(
            {
                "data": {"message": _("Message sent successfully")},
                "meta": {"success": True},
            }
        )

    except Exception as e:
        return (
            jsonify({"data": [], "meta": {"success": False, "errors": str(e)}}),
            500,
        )


@app.route("/routes", methods=["GET"])
@ensure_authorized
def routes():
    """Returns available routes on the API."""

    routes = {"GET": [], "POST": [], "PUT": [], "PATCH": [], "DELETE": []}

    # Iterating through all routes/rules
    for rule in app.url_map.iter_rules():
        # Available data: rule, rule.endpoint, rule.methods, rule.arguments
        # Getting the route parts and formatting
        parts = []
        for p in str(rule).split("/"):
            p = re.sub("[<>]", "", p)
            if ":" in p:
                p = ":" + p.split(":")[1]
            parts.append(p)
        route = "/".join(parts)
        if "GET" in rule.methods:
            routes["GET"].append(route)
        if "POST" in rule.methods:
            routes["POST"].append(route)
        if "PUT" in rule.methods:
            routes["PUT"].append(route)
        if "PATCH" in rule.methods:
            routes["PATCH"].append(route)
        if "DELETE" in rule.methods:
            routes["DELETE"].append(route)
    # Returning the list with methods, routes and arguments
    return jsonify(routes)


@app.errorhandler(404)
def not_found(error):
    """Sample HTTP resource error handling."""
    return (
        jsonify(
            {"data": [], "meta": {"success": False, "errors": _("Resource not found.")}}
        ),
        404,
    )


@app.errorhandler(413)
def content_size_handler(e):
    """Sample content size error handling."""
    return (
        jsonify(
            {
                "data": [],
                "meta": {
                    "success": False,
                    "errors": (_("Content too large"), e.description),
                },
            }
        ),
        413,
    )


@app.errorhandler(429)
def ratelimit_handler(e):
    """Sample rate limit error handling."""
    return (
        jsonify(
            {
                "data": [],
                "meta": {
                    "success": False,
                    "errors": (_("Ratelimit exceeded"), f"{e.description}."),
                },
            }
        ),
        429,
    )


# Engine and Session for executing queries with ORM
engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    echo=True,
    future=True,
    connect_args=DATABASE_CONNECT_OPTIONS,
)
# Defining a sessionmaker to use on modules routes
AppSession = sessionmaker(engine)

# Import and registering blueprints
from app.modules.users.controllers import *
from app.modules.log.controllers import *
from app.modules.document.controllers import *
from app.modules.notification.controllers import *
from app.modules.commons.controllers import *

# Users modules
app.register_blueprint(mod_auth)
app.register_blueprint(mod_profile)
app.register_blueprint(mod_user)
app.register_blueprint(mod_role)
app.register_blueprint(mod_role_api_route)
app.register_blueprint(mod_role_web_action)
app.register_blueprint(mod_role_mobile_action)
# Notification modules
app.register_blueprint(mod_notification)
# Commons modules
app.register_blueprint(mod_city)
app.register_blueprint(mod_uf)
# Document modules
app.register_blueprint(mod_document_category)
app.register_blueprint(mod_document)
app.register_blueprint(mod_document_model)
app.register_blueprint(mod_document_sharing)
# Log modules
app.register_blueprint(mod_log)

# Build the database:
# This can create the database file using SQLAlchemy or the selected SQL database/driver
# However, since we're using Alembic for database migrations, we'll only call this when testing
if app.config["TESTING"]:
    db.create_all()
