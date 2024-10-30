"""Models for the documents module."""

import os

from config import STORAGE_DRIVER, tz
from app import db
from app.modules.users.models import *


def default_object_string(object, timezone=tz):
    """Function to format an object (like datetime/date) to a string."""

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


class Base(db.Model):
    """Base application model for other database tables to inherit."""

    __abstract__ = True

    # Defining base columns
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )


class DocumentCategory(Base):
    __tablename__ = "document_category"

    # Basic data
    code = db.Column(db.String(128), nullable=False, unique=True)
    name = db.Column(db.String(256), nullable=False)

    # Relationships
    document = db.relationship("Document", lazy="select", backref="document_category")
    # model_name = db.relationship('ModelName', lazy='select', backref='document_category')

    def __init__(self, code, name):
        self.code = code
        self.name = name

    def __repr__(self):
        return "<DocumentCategory %r>" % (self.code)

    # Returning data as dict
    def as_dict(self, timezone=tz):
        data = {
            c.name: default_object_string(getattr(self, c.name), timezone)
            for c in self.__table__.columns
        }
        # Add related tables
        for c in self.__dict__:
            if "app" in str(type(self.__dict__[c])):
                data[c] = self.__dict__[c].as_dict(timezone)
        return data


class Document(Base):
    __tablename__ = "document"

    # Basic data
    code = db.Column(db.String(128), nullable=False, unique=True)
    description = db.Column(db.String(256), nullable=False)
    observations = db.Column(db.String(512), nullable=True)
    expires_at = db.Column(db.Date, nullable=True)
    alert_email = db.Column(db.String(1024), nullable=True)
    alert = db.Column(db.Integer, nullable=False)
    days_to_alert = db.Column(db.Integer, nullable=True)

    # Relationships and status
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    document_category_id = db.Column(
        db.Integer, db.ForeignKey("document_category.id"), nullable=True
    )

    # File
    file_url = db.Column(db.String(1024))
    file_name = db.Column(db.String(512))
    file_content_type = db.Column(db.String(128))
    file_size = db.Column(db.String(128))
    file_updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )
    file_thumbnail_url = db.Column(db.String(1024))
    file_thumbnail_file_size = db.Column(db.String(128))

    # Relationships
    document_model = db.relationship("DocumentModel", lazy="select", backref="document")
    document_sharing = db.relationship(
        "DocumentSharing", lazy="select", backref="document"
    )
    # model_name = db.relationship('ModelName', lazy='select', backref='document')

    def __init__(
        self,
        code,
        description,
        alert,
        user_id,
        file_url,
        file_name,
        file_content_type,
        file_size,
        file_updated_at,
        file_thumbnail_url=None,
        file_thumbnail_file_size=None,
        observations=None,
        expires_at=None,
        alert_email=None,
        days_to_alert=None,
        document_category_id=None,
    ):
        self.code = code
        self.description = description
        self.observations = observations
        self.expires_at = expires_at
        self.alert_email = alert_email
        self.alert = alert
        self.days_to_alert = days_to_alert
        self.user_id = user_id
        self.document_category_id = document_category_id
        self.file_url = file_url
        self.file_name = file_name
        self.file_content_type = file_content_type
        self.file_size = file_size
        self.file_updated_at = file_updated_at
        self.file_thumbnail_url = file_thumbnail_url
        self.file_thumbnail_file_size = file_thumbnail_file_size

    def __repr__(self):
        return "<Document %r>" % (self.code)

    # Defining URL according to the storage driver
    def full_file_url(self):
        if self.file_url is not None and self.file_url != "":
            if STORAGE_DRIVER == "disk":
                return f'{os.environ.get("APP_API_URL")}/files/{self.file_url}'
            elif STORAGE_DRIVER == "s3":
                return (
                    "https://"
                    + os.environ.get("AWS_BUCKET")
                    + ".s3."
                    + os.environ.get("AWS_REGION")
                    + ".amazonaws.com/"
                    + self.file_url
                )
        else:
            return None

    # Defining URL according to the storage driver
    def full_file_thumbnail_url(self):
        if self.file_thumbnail_url is not None and self.file_thumbnail_url != "":
            if STORAGE_DRIVER == "disk":
                return (
                    f'{os.environ.get("APP_API_URL")}/files/{self.file_thumbnail_url}'
                )
            elif STORAGE_DRIVER == "s3":
                return (
                    "https://"
                    + os.environ.get("AWS_BUCKET")
                    + ".s3."
                    + os.environ.get("AWS_REGION")
                    + ".amazonaws.com/"
                    + self.file_thumbnail_url
                )
        else:
            return None

    # Returning data as dict
    def as_dict(self, timezone=tz):
        data = {
            c.name: default_object_string(getattr(self, c.name), timezone)
            for c in self.__table__.columns
        }
        data["file_url"] = self.full_file_url()
        data["file_thumbnail_url"] = self.full_file_thumbnail_url()
        # Add the related tables
        for c in self.__dict__:
            if "app" in str(type(self.__dict__[c])):
                data[c] = self.__dict__[c].as_dict(timezone)
        return data


class DocumentModel(Base):
    __tablename__ = "document_model"

    # Basic data
    model_name = db.Column(db.String(256), nullable=False)

    # Relationships and status
    model_id = db.Column(db.Integer, nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey("document.id"), nullable=False)

    # Relationships
    # model_name = db.relationship('ModelName', lazy='select', backref='document_model')

    def __init__(self, model_name, model_id, document_id):
        self.model_name = model_name
        self.model_id = model_id
        self.document_id = document_id

    def __repr__(self):
        return "<DocumentModel %r>" % (self.id)

    # Returning data as dict
    def as_dict(self, timezone=tz):
        data = {
            c.name: default_object_string(getattr(self, c.name), timezone)
            for c in self.__table__.columns
        }
        # Adding the related tables
        for c in self.__dict__:
            if "app" in str(type(self.__dict__[c])):
                data[c] = self.__dict__[c].as_dict(timezone)
        return data


class DocumentSharing(Base):
    __tablename__ = "document_sharing"

    # Relationships and status
    shared_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey("document.id"), nullable=False)

    # Relationships
    # model_name = db.relationship('ModelName', lazy='select', backref='document_sharing')

    def __init__(self, shared_user_id, document_id):
        self.shared_user_id = shared_user_id
        self.document_id = document_id

    def __repr__(self):
        return "<DocumentSharing %r>" % (self.id)

    # Returning data as dict
    def as_dict(self, timezone=tz):
        data = {
            c.name: default_object_string(getattr(self, c.name), timezone)
            for c in self.__table__.columns
        }
        # Adding the related tables
        for c in self.__dict__:
            if "app" in str(type(self.__dict__[c])):
                data[c] = self.__dict__[c].as_dict(timezone)
        return data
