# -*- coding: utf-8 -*-

# Getting config data
from config import tz

# Import the database object (db) from the main application module
from app import db


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


# Define a UF model using Base columns
class UF(Base):
    __tablename__ = "uf"

    # Basic data
    code = db.Column(db.String(128), nullable=False, unique=True)
    name = db.Column(db.String(128), nullable=False)

    # Relationships
    city = db.relationship("City", lazy="select", backref="uf")
    # model_name = db.relationship('ModelName', lazy='select', backref='uf')

    # New instance instantiation procedure
    def __init__(self, code, name):
        self.code = code
        self.name = name

    def __repr__(self):
        return "<UF %r>" % (self.code)

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


# Define a city model using Base columns
class City(Base):
    __tablename__ = "city"

    # Basic data
    name = db.Column(db.String(128), nullable=False)

    # Relationships and status
    uf_id = db.Column(db.Integer, db.ForeignKey("uf.id"), nullable=False)

    # Relationships
    # model_name = db.relationship('ModelName', lazy='select', backref='city')

    # New instance instantiation procedure
    def __init__(self, name, uf_id):
        self.name = name
        self.uf_id = uf_id

    def __repr__(self):
        return "<City %r>" % (self.name)

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
