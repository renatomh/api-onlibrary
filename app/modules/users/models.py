# -*- coding: utf-8 -*-

# Import flask dependencies
import os

# Getting config data
from config import tz

# Import the database object (db) from the main application module
from app import db

# JWT for token generation
import jwt

# Library to deal with dates, UTC, etc.
from datetime import datetime, timedelta


# Function to format an object (like datetime/date) to a string
def default_object_string(object, timezone=tz):
    if str(type(object)) == "<class 'datetime.datetime'>":
        try:
            return (
                tz.localize(object).astimezone(timezone).strftime("%Y-%m-%dT%H:%M:%S%z")
            )
        except:
            return object.astimezone(timezone).strftime("%Y-%m-%dT%H:%M:%S%z")
    elif str(type(object)) == "<class 'datetime.date'>":
        return object.strftime("%Y-%m-%d")
    return object


# Define a base model for other database tables to inherit
class Base(db.Model):
    __abstract__ = True

    # Defining base columns
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )


# Define a User model using Base columns
class User(Base):
    __tablename__ = "user"

    # User Name
    name = db.Column(db.String(128), nullable=False)

    # Identification Data: email, password, etc.
    username = db.Column(db.String(128), nullable=False, unique=True)
    email = db.Column(db.String(128), nullable=True)
    hashpass = db.Column(db.String(192), nullable=False)
    avatar_url = db.Column(db.String(1024), nullable=True)
    avatar_thumbnail_url = db.Column(db.String(1024), nullable=True)
    last_login_at = db.Column(db.DateTime, nullable=True)
    socketio_sid = db.Column(db.String(256), nullable=True)
    fcm_token = db.Column(db.String(512), nullable=True)

    # Authorisation Data: role & status
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False)
    is_active = db.Column(db.Integer, nullable=False)
    is_verified = db.Column(db.Integer, nullable=False)

    # Relationships
    document = db.relationship("Document", lazy="select", backref="user")
    log = db.relationship("Log", lazy="select", backref="user")
    document_sharing = db.relationship(
        "DocumentSharing", lazy="select", backref="shared_user"
    )
    notification = db.relationship("Notification", lazy="select", backref="user")

    # New instance instantiation procedure
    def __init__(
        self,
        name,
        username,
        hashpass,
        email=None,
        role_id=2,
        is_active=0,
        is_verified=0,
    ):
        self.name = name
        self.username = username
        self.email = email
        self.hashpass = hashpass
        self.role_id = role_id
        self.is_active = is_active
        self.is_verified = is_verified

    def __repr__(self):
        return "<User %r>" % (self.name)

    # Defining URL according to the storage driver
    def full_avatar_url(self):
        if self.avatar_url is not None and self.avatar_url != "":
            if os.environ.get("STORAGE_DRIVER") == "disk":
                return f'{os.environ.get("APP_API_URL")}/files/{self.avatar_url}'
            elif os.environ.get("STORAGE_DRIVER") == "s3":
                return f'https://{os.environ.get("AWS_BUCKET")}.s3.{os.environ.get("AWS_REGION")}.amazonaws.com/{self.avatar_url}'
        else:
            return None

    # Defining URL according to the storage driver
    def full_avatar_thumbnail_url(self):
        if self.avatar_thumbnail_url is not None and self.avatar_thumbnail_url != "":
            if os.environ.get("STORAGE_DRIVER") == "disk":
                return (
                    f'{os.environ.get("APP_API_URL")}/files/{self.avatar_thumbnail_url}'
                )
            elif os.environ.get("STORAGE_DRIVER") == "s3":
                return f'https://{os.environ.get("AWS_BUCKET")}.s3.{os.environ.get("AWS_REGION")}.amazonaws.com/{self.avatar_thumbnail_url}'
        else:
            return None

    # Returning data as dict
    def as_dict(self, timezone=tz):
        # We also remove the password
        data = {
            c.name: default_object_string(getattr(self, c.name), timezone)
            for c in self.__table__.columns
            if c.name != "hashpass"
        }
        data["avatar_url"] = self.full_avatar_url()
        data["avatar_thumbnail_url"] = self.full_avatar_thumbnail_url()
        # Adding the related tables
        for c in self.__dict__:
            if "app" in str(type(self.__dict__[c])):
                data[c] = self.__dict__[c].as_dict(timezone)
            # For many-to-many relationships
            if "InstrumentedList" in str(type(self.__dict__[c])):
                # Adding the itens IDs
                data[c + "_ids"] = [i.id for i in self.__dict__[c]]
        return data

    # Enconding the verification token
    def encode_verif_token(self, id):
        try:
            payload = {"iat": datetime.utcnow(), "sub": id}
            return jwt.encode(payload, os.environ.get("APP_SECRET"), algorithm="HS256")
        except Exception as e:
            return e

    # Decoding the verification JWT
    @staticmethod
    def decode_verif_token(token):
        try:
            # For newer versions of PyJWT (>= 2.0.0), we must add the 'algorithms' arg
            payload = jwt.decode(
                token, os.environ.get("APP_SECRET"), algorithms=["HS256"]
            )
            return payload["sub"]
        except jwt.InvalidTokenError:
            return "Invalid token. Please verify and contact the system admin."

    # Enconding the authentication token
    def encode_auth_token(self, id):
        try:
            payload = {
                "exp": datetime.utcnow() + timedelta(hours=2, minutes=30, seconds=0),
                "iat": datetime.utcnow(),
                "sub": id,
            }
            return jwt.encode(payload, os.environ.get("APP_SECRET"), algorithm="HS256")
        except Exception as e:
            return e

    # Decoding the authentication JWT
    @staticmethod
    def decode_auth_token(token):
        try:
            # For newer versions of PyJWT (>= 2.0.0), we must add the 'algorithms' arg
            payload = jwt.decode(
                token, os.environ.get("APP_SECRET"), algorithms=["HS256"]
            )
            return payload["sub"]
        except jwt.ExpiredSignatureError:
            return "Token expired. Please log in again."
        except jwt.InvalidTokenError:
            return "Invalid token. Please log in again."


# Define a Role model using Base columns
class Role(Base):
    __tablename__ = "role"

    # Role Name
    name = db.Column(db.String(128), nullable=False)

    # Relationships
    user = db.relationship("User", lazy="select", backref="role")
    # We'll cascade delete the APi routes, web and mobile actions when removing the role
    role_api_route = db.relationship(
        "RoleAPIRoute", lazy="select", backref="role", cascade="all, delete"
    )
    role_web_action = db.relationship(
        "RoleWebAction", lazy="select", backref="role", cascade="all, delete"
    )
    role_mobile_action = db.relationship(
        "RoleMobileAction", lazy="select", backref="role", cascade="all, delete"
    )

    # New instance instantiation procedure
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<Role %r>" % (self.name)

    # Returning data as dict
    def as_dict(self, timezone=tz):
        # We also remove the password
        data = {
            c.name: default_object_string(getattr(self, c.name), timezone)
            for c in self.__table__.columns
        }
        # Adding the related tables
        for c in self.__dict__:
            if "app" in str(type(self.__dict__[c])):
                data[c] = self.__dict__[c].as_dict(timezone)
        return data


# Define a Role API Route model using Base columns
class RoleAPIRoute(Base):
    __tablename__ = "role_api_route"

    # Basic data
    route = db.Column(db.String(512), nullable=False)
    method = db.Column(db.String(8), nullable=False)

    # Relationships and status
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False)

    # Relationships
    # model_name = db.relationship('ModelName', lazy='select', backref='role_api_route')

    # New instance instantiation procedure
    def __init__(self, route, method, role_id):
        self.route = route
        self.method = method
        self.role_id = role_id

    def __repr__(self):
        return "<RoleAPIRoute %r>" % (self.id)

    # Returning data as dict
    def as_dict(self, timezone=tz):
        # We also remove the password
        data = {
            c.name: default_object_string(getattr(self, c.name), timezone)
            for c in self.__table__.columns
        }
        # Adding the related tables
        for c in self.__dict__:
            if "app" in str(type(self.__dict__[c])):
                data[c] = self.__dict__[c].as_dict(timezone)
        return data


# Define a Role web action model using Base columns
class RoleWebAction(Base):
    __tablename__ = "role_web_action"

    # Basic data
    action = db.Column(db.String(512), nullable=False)

    # Relationships and status
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False)

    # Relationships
    # model_name = db.relationship('ModelName', lazy='select', backref='role_web_action')

    # New instance instantiation procedure
    def __init__(self, action, role_id):
        self.action = action
        self.role_id = role_id

    def __repr__(self):
        return "<RoleWebAction %r>" % (self.id)

    # Returning data as dict
    def as_dict(self, timezone=tz):
        # We also remove the password
        data = {
            c.name: default_object_string(getattr(self, c.name), timezone)
            for c in self.__table__.columns
        }
        # Adding the related tables
        for c in self.__dict__:
            if "app" in str(type(self.__dict__[c])):
                data[c] = self.__dict__[c].as_dict(timezone)
        return data


# Define a Role mobile action model using Base columns
class RoleMobileAction(Base):
    __tablename__ = "role_mobile_action"

    # Basic data
    action = db.Column(db.String(512), nullable=False)

    # Relationships and status
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False)

    # Relationships
    # model_name = db.relationship('ModelName', lazy='select', backref='role_mobile_action')

    # New instance instantiation procedure
    def __init__(self, action, role_id):
        self.action = action
        self.role_id = role_id

    def __repr__(self):
        return "<RoleMobileAction %r>" % (self.id)

    # Returning data as dict
    def as_dict(self, timezone=tz):
        # We also remove the password
        data = {
            c.name: default_object_string(getattr(self, c.name), timezone)
            for c in self.__table__.columns
        }
        # Adding the related tables
        for c in self.__dict__:
            if "app" in str(type(self.__dict__[c])):
                data[c] = self.__dict__[c].as_dict(timezone)
        return data
