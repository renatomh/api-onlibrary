"""Models for the notifications module."""

from config import tz
from app import db
from app.modules.users.models import *
from app.modules.settings.models import *


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


class Notification(Base):
    __tablename__ = "notification"

    # Basic data
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(1024), nullable=False)
    web_action = db.Column(db.String(512), nullable=True)
    mobile_action = db.Column(db.String(512), nullable=True)
    read_at = db.Column(db.DateTime, nullable=True)

    # Relationships and status
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    is_read = db.Column(db.Integer, nullable=False, default=0)

    # Relationships
    # model_name = db.relationship('ModelName', lazy='select', backref='notification')

    def __init__(
        self, title, description, user_id, web_action=None, mobile_action=None
    ):
        self.title = title
        self.description = description
        self.user_id = user_id
        self.web_action = web_action
        self.mobile_action = mobile_action

    def __repr__(self):
        return "<Notification %r>" % (self.id)

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
