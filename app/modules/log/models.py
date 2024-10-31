"""Models for the logs module."""

from config import tz
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


class Log(Base):
    __tablename__ = "log"

    # Basic data
    model_name = db.Column(db.String(256), nullable=False)
    ip_address = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(1024), nullable=False)

    # Relationships and status
    model_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Relationships
    # model_name = db.relationship('ModelName', lazy='select', backref='log')

    def __init__(self, model_name, ip_address, description, model_id, user_id):
        self.model_name = model_name
        self.ip_address = ip_address
        self.description = description
        self.model_id = model_id
        self.user_id = user_id

    def __repr__(self):
        return "<Log %r>" % (self.id)

    # Returning data as dict
    def as_dict(self, timezone=tz):
        data = {
            c.name: default_object_string(getattr(self, c.name), timezone)
            for c in self.__table__.columns
        }
        # Add the related tables
        for c in self.__dict__:
            if "app" in str(type(self.__dict__[c])):
                data[c] = self.__dict__[c].as_dict(timezone)
        return data
