"""Models for the commons module."""

from config import tz
from app import db


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


class UF(Base):
    __tablename__ = "uf"

    # Basic data
    code = db.Column(db.String(128), nullable=False, unique=True)
    name = db.Column(db.String(128), nullable=False)

    # Relationships
    city = db.relationship("City", lazy="select", backref="uf")
    # model_name = db.relationship('ModelName', lazy='select', backref='uf')

    def __init__(self, code, name):
        self.code = code
        self.name = name

    def __repr__(self):
        return "<UF %r>" % (self.code)

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


class City(Base):
    __tablename__ = "city"

    # Basic data
    name = db.Column(db.String(128), nullable=False)

    # Relationships and status
    uf_id = db.Column(db.Integer, db.ForeignKey("uf.id"), nullable=False)

    # Relationships
    # model_name = db.relationship('ModelName', lazy='select', backref='city')

    def __init__(self, name, uf_id):
        self.name = name
        self.uf_id = uf_id

    def __repr__(self):
        return "<City %r>" % (self.name)

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
