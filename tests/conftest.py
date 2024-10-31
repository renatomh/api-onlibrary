"""
Script to create testing config.

Refs:
    https://flask.palletsprojects.com/en/2.2.x/testing/
    https://flask.palletsprojects.com/en/2.2.x/tutorial/tests/
"""

import os

import pytest
from flask import Flask
from flask_babel import Babel
from sqlalchemy import create_engine

os.environ["SQL_DRIVER"] = "sqlite"
os.environ["TESTING"] = "true"
os.environ["MAIL_DRIVER"] = "test"

from app import db

# Blueprints
from app.modules.users.controllers import *
from app.modules.commons.controllers import *
from app.modules.log.controllers import *
from app.modules.notification.controllers import *
from app.modules.document.controllers import *


@pytest.fixture()
def app():
    # Initializing and configuring
    app = Flask(__name__, template_folder="../app/templates")
    app.config.from_object("config")
    app.config.update({"TESTING": True})

    # Tranlsation features to app
    babel = Babel(app)

    # Selecting language according to 'Accept-Language' header from incoming request
    @babel.localeselector
    def get_locale():
        return request.accept_languages.best_match(app.config["LANGUAGES"].keys())

    # Initializing database within app context
    with app.app_context():
        db.init_app(app)

    # Recreating test database
    db.drop_all()
    db.create_all()

    # Preloading default data to the database
    engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
    with engine.begin() as conn:
        dbapi_conn = conn.connection
        with open("default-data-test.sql", encoding="utf8") as f:
            dbapi_conn.executescript(f.read())

    # Registering blueprints which will be tested
    app.register_blueprint(mod_auth)
    app.register_blueprint(mod_profile)
    app.register_blueprint(mod_user)
    app.register_blueprint(mod_role)
    app.register_blueprint(mod_role_api_route)
    app.register_blueprint(mod_role_web_action)
    app.register_blueprint(mod_role_mobile_action)
    app.register_blueprint(mod_log)
    app.register_blueprint(mod_notification)
    app.register_blueprint(mod_document_category)
    app.register_blueprint(mod_document)
    app.register_blueprint(mod_document_model)
    app.register_blueprint(mod_document_sharing)
    app.register_blueprint(mod_uf)
    app.register_blueprint(mod_city)

    # Generating the app
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
