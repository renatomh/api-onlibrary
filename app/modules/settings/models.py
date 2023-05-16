# -*- coding: utf-8 -*-

# Getting config data
from config import tz

# Import the database object (db) from the main application module
from app import db

# Function to format an object (like datetime/date) to a string
def default_object_string(object, timezone=tz):
    if str(type(object)) == "<class 'datetime.datetime'>":
        try: return tz.localize(object).astimezone(timezone).strftime('%Y-%m-%dT%H:%M:%S%z')
        except: return object.astimezone(timezone).strftime('%Y-%m-%dT%H:%M:%S%z')
    elif str(type(object)) == "<class 'datetime.date'>":
        return object.strftime("%Y-%m-%d")
    return object

# Define a base model for other database tables to inherit
class Base(db.Model):
    __abstract__ = True

    # Defining base columns
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(),
                                        onupdate=db.func.current_timestamp())

# Define a library model using Base columns
class Library(Base):
    __tablename__ = 'library'

    # Basic data
    name = db.Column(db.String(128), nullable=False, unique=True)

    # Identification Data: email, password, etc.
    cnpj = db.Column(db.String(18))
    cpf = db.Column(db.String(18))

    # Relationships
    city_id = db.Column(db.Integer, db.ForeignKey('city.id'), nullable=True)
    user = db.relationship('User', lazy='select', backref='library')
    document = db.relationship('Document', lazy='select', backref='library')
    document_category = db.relationship('DocumentCategory', lazy='select', backref='library')
    # model_name = db.relationship('ModelName', lazy='select', backref='library')

    # New instance instantiation procedure
    def __init__(self, name, cnpj=None, cpf=None, city_id=None):
        self.name = name
        self.cnpj = cnpj
        self.cpf = cpf
        self.city_id = city_id

    def __repr__(self):
        return '<Library %r>' % (self.name)

    # Returning data as dict
    def as_dict(self, timezone=tz):
        # We also remove the password
        data = {c.name: default_object_string(getattr(self, c.name), timezone)
                for c in self.__table__.columns}
        # Adding the related tables
        for c in self.__dict__:
            if 'app' in str(type(self.__dict__[c])):
                data[c] = self.__dict__[c].as_dict(timezone)
        return data

# Define a city model using Base columns
class City(Base):
    __tablename__ = 'city'

    # Basic data
    name = db.Column(db.String(128), nullable=False)
    uf = db.Column(db.String(16), nullable=False)

    # Relationships
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=False)
    library = db.relationship('Library', lazy="select", backref='city')

    # New instance instantiation procedure
    def __init__(self, name, uf, country_id=1):
        self.name = name
        self.uf = uf
        self.country_id = country_id

    def __repr__(self):
        return '<City %r>' % (self.name)

    # Returning data as dict
    def as_dict(self, timezone=tz):
        # We also remove the password
        data = {c.name: default_object_string(getattr(self, c.name), timezone)
                for c in self.__table__.columns}
        # Adding the related tables
        for c in self.__dict__:
            if 'app' in str(type(self.__dict__[c])):
                data[c] = self.__dict__[c].as_dict(timezone)
        return data

# Define a country model using Base columns
class Country(Base):
    __tablename__ = 'country'

    # Basic data
    name = db.Column(db.String(128), nullable=False, unique=True)
    code = db.Column(db.String(8), nullable=True)

    # Relationships
    city = db.relationship('City', lazy="select", backref='country')
    author = db.relationship('Author', lazy="select", backref='country')
    publisher = db.relationship('Publisher', lazy="select", backref='publisher')

    # New instance instantiation procedure
    def __init__(self, name, code=None):
        self.name = name
        self.code = code

    def __repr__(self):
        return '<Country %r>' % (self.name)

    # Returning data as dict
    def as_dict(self, timezone=tz):
        # We also remove the password
        data = {c.name: default_object_string(getattr(self, c.name), timezone)
                for c in self.__table__.columns}
        # Adding the related tables
        for c in self.__dict__:
            if 'app' in str(type(self.__dict__[c])):
                data[c] = self.__dict__[c].as_dict(timezone)
        return data
