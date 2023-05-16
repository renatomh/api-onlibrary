# -*- coding: utf-8 -*-

# Import flask dependencies
import os

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

# Define an author model using Base columns
class Author(Base):
    __tablename__ = 'author'

    # Basic data
    name = db.Column(db.String(256), nullable=False)
    birth_date = db.Column(db.Date, nullable=True)
    death_date = db.Column(db.Date, nullable=True)
    biography = db.Column(db.String(1024), nullable=True)
    external_photo_url = db.Column(db.String(1024))

    # Photo
    photo_url = db.Column(db.String(1024))
    photo_file_name = db.Column(db.String(512))
    photo_file_content_type = db.Column(db.String(128))
    photo_file_size = db.Column(db.String(128))
    photo_updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(),
                                        onupdate=db.func.current_timestamp())
    photo_thumbnail_url = db.Column(db.String(1024))
    photo_thumbnail_file_size = db.Column(db.String(128))

    # Relationship fileds
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=True)
    
    # Relationships
    # model_name = db.relationship('ModelName', lazy='select', backref='author')

    # New instance instantiation procedure
    def __init__(self, name, birth_date=None, death_date=None, biography=None,
        external_photo_url=None, country_id=None):
        self.name = name
        self.birth_date = birth_date
        self.death_date = death_date
        self.biography = biography
        self.external_photo_url = external_photo_url
        self.country_id = country_id

    def __repr__(self):
        return '<Author %r>' % (self.name)
    
    # Defining URL according to the storage driver
    def full_photo_url(self):
        if self.photo_url and self.photo_url != '':
            if os.environ.get('STORAGE_DRIVER') == 'disk':
                return f'{os.environ.get("APP_API_URL")}/files/{self.photo_url}'
            elif os.environ.get('STORAGE_DRIVER') == 's3':
                return f'https://{os.environ.get("AWS_BUCKET")}.s3.{os.environ.get("AWS_REGION")}.amazonaws.com/{self.photo_url}'
        else:
            return None

    # Defining URL according to the storage driver
    def full_photo_thumbnail_url(self):
        if self.photo_thumbnail_url and self.photo_thumbnail_url != '':
            if os.environ.get('STORAGE_DRIVER') == 'disk':
                return f'{os.environ.get("APP_API_URL")}/files/{self.photo_thumbnail_url}'
            elif os.environ.get('STORAGE_DRIVER') == 's3':
                return f'https://{os.environ.get("AWS_BUCKET")}.s3.{os.environ.get("AWS_REGION")}.amazonaws.com/{self.photo_thumbnail_url}'
        else:
            return None

    # Returning data as dict
    def as_dict(self, timezone=tz):
        # We also remove the password
        data = {c.name: default_object_string(getattr(self, c.name), timezone)
                for c in self.__table__.columns}
        data['photo_url'] = self.full_photo_url()
        data['photo_thumbnail_url'] = self.full_photo_thumbnail_url()
        # Adding the related tables
        for c in self.__dict__:
            if 'app' in str(type(self.__dict__[c])):
                data[c] = self.__dict__[c].as_dict(timezone)
        return data

# Define a publisher model using Base columns
class Publisher(Base):
    __tablename__ = 'publisher'

    # Basic data
    name = db.Column(db.String(128), nullable=False, unique=True)
    description = db.Column(db.String(256), nullable=True)

    # Relationship fileds
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=True)
    
    # Relationships
    # model_name = db.relationship('ModelName', lazy='select', backref='publisher')

    # New instance instantiation procedure
    def __init__(self, name, description=None, country_id=None):
        self.name = name
        self.description = description
        self.country_id = country_id

    def __repr__(self):
        return '<Publisher %r>' % (self.name)

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
