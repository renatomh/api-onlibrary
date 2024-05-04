# Define the application directory
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Statement for enabling the development environment
DEBUG = True
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Setting up the '.env' file with environment variables
from dotenv import load_dotenv

load_dotenv(".env")

# Setting the flag for testing environment
# The "TESTING" variable won't be set in the ".env" file, but directly in the
# Tests configration file ("conftest.py")
TESTING = os.getenv("TESTING", "False").lower() == "true"

# Defining the default timezone for the application
import pytz

# If environment timezone name changes, all datetimes on database might have to be corrected
tz = pytz.timezone(os.getenv("TZ", "UTC"))

# This module is required for usernames and passwords with special characters
from urllib.parse import quote

# Define the database
if os.environ.get("SQL_DRIVER") == "sqlite":
    # 'check_same_thread=False' arg is required when using SQLlite3 to avoid 'ProgrammingError'
    SQLALCHEMY_DATABASE_URI = (
        "sqlite:///"
        + os.path.join(BASE_DIR, os.environ.get("SQL_DB") + ".db")
        + "?check_same_thread=False"
    )
elif os.environ.get("SQL_DRIVER") == "mysql":
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("SQL_DRIVER")
        + "+pymysql://"
        + quote(os.environ.get("SQL_USER"))
        + ":"
        + quote(os.environ.get("SQL_PASS"))
        + "@"
        + os.environ.get("SQL_HOST")
        + ":"
        + os.environ.get("SQL_PORT")
        + "/"
        + os.environ.get("SQL_DB")
    )
elif os.environ.get("SQL_DRIVER") == "postgresql":
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("SQL_DRIVER")
        + "+psycopg2://"
        + quote(os.environ.get("SQL_USER"))
        + ":"
        + quote(os.environ.get("SQL_PASS"))
        + "@"
        + os.environ.get("SQL_HOST")
        + ":"
        + os.environ.get("SQL_PORT")
        + "/"
        + os.environ.get("SQL_DB")
    )
# Currently, this is not available when running on Docker containers, since there are some troubles when
# installing pyodbc on the Docker images
elif os.environ.get("SQL_DRIVER") == "mssql":
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("SQL_DRIVER")
        + "+pyodbc://"
        + quote(os.environ.get("SQL_USER"))
        + ":"
        + quote(os.environ.get("SQL_PASS"))
        + "@"
        + os.environ.get("SQL_HOST")
        + ":"
        + os.environ.get("SQL_PORT")
        + "/"
        + os.environ.get("SQL_DB")
        + "?driver="
        + os.environ.get("ODBC_DRIVER")
    )
DATABASE_CONNECT_OPTIONS = {}
# Option to try avoiding problems of connection with SQL server being lost
SQLALCHEMY_ENGINE_OPTIONS = {"pool_recycle": 280, "pool_pre_ping": True}
# Pool size option is not available for SQLite
if os.environ.get("SQL_DRIVER") != "sqlite":
    SQLALCHEMY_ENGINE_OPTIONS["pool_size"] = 100

# Available languages for internationalization/localization (i18n, l10n)
LANGUAGES = {
    "en": "English",
    "pt": "Portuguese",
    "es": "Spanish",
}

# Define output folder path
OUTPUT_FOLDER = os.path.join(BASE_DIR, "app" + os.sep + "output")
# Define static folder path
STATIC_FOLDER = os.path.join(BASE_DIR, "app" + os.sep + "static")
# Define uploads folder path
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
UPLOAD_TEMP_FOLDER = os.path.join(BASE_DIR, "uploads" + os.sep + "tmp")

# Defining max size and allowed extensions
MAX_CONTENT_LENGTH = 16 * 1000 * 1000  # MB * 1000 * 1000
ALLOWED_FILE_EXTENSIONS = [
    "txt",
    "pdf",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "csv",
    "zip",
    "rar",
]
ALLOWED_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "gif"]
ALLOWED_VIDEO_EXTENSIONS = ["mp4", "m4v", "mkv", "mov", "wmv", "avi"]
# Extending files to allow image and video formats
ALLOWED_FILE_EXTENSIONS.extend(ALLOWED_IMAGE_EXTENSIONS)
ALLOWED_FILE_EXTENSIONS.extend(ALLOWED_VIDEO_EXTENSIONS)

# Defining storage driver
STORAGE_DRIVER = os.environ.get("STORAGE_DRIVER")

# Defining mail driver and details
MAIL_DRIVER = os.environ.get("MAIL_DRIVER")
MAIL_USER = os.environ.get("MAIL_USER")
MAIL_PASS = os.environ.get("MAIL_PASS")

# Setting up allowed e-mail domains for registering
ALLOWED_EMAIL_DOMAINS = [
    "gmail.com",
    "*",  # If we want to allow every domain, we can add the wildcard
]

# Application threads. A common general assumption is
# using 2 per available processor cores - to handle
# incoming requests using one and performing background
# operations using the other.
THREADS_PER_PAGE = 2

# Enable protection against *Cross-site Request Forgery (CSRF)*
CSRF_ENABLED = True

# Use a secure, unique and absolutely secret key for
# signing the data.
CSRF_SESSION_KEY = os.environ.get("APP_SECRET")

# Secret key for signing cookies
SECRET_KEY = os.environ.get("APP_SECRET")

# Defining serve port number and host
PORT = os.environ.get("PORT")
HOST = os.environ.get("HOST")
