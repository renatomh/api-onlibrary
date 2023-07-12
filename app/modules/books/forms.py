# -*- coding: utf-8 -*-

# Import Form
from wtforms import Form

# Import JSON extension for forms
import wtforms_json

# Import Form elements such as TextField and BooleanField (optional)
from wtforms import TextField, RadioField, IntegerField, FloatField # BooleanField

# Import Form validators
from wtforms.validators import InputRequired, Optional, Length
from app.modules.utils import DateField

# Initiating JSON for forms
wtforms_json.init()

# Define the create author form (WTForms)
class CreateAuthorForm(Form):
    name = TextField('Name', [
        InputRequired(message='You must provide a name.'),
        Length(max=256)
    ])
    birth_date = DateField('Birth Date', [Optional()])
    death_date = DateField('Death Date', [Optional()])
    biography = TextField('Biography', [
        Optional(),
        Length(max=1024)
    ])
    external_photo_url = TextField('External Photo URL', [
        Optional(),
        Length(max=1024)
    ])
    country_id = IntegerField('Country ID', [Optional()])

# Define the update author form (WTForms)
class UpdateAuthorForm(Form):
    name = TextField('Name', [
        Optional(),
        Length(max=256)
    ])
    birth_date = DateField('Birth Date', [Optional()])
    death_date = DateField('Death Date', [Optional()])
    biography = TextField('Biography', [
        Optional(),
        Length(max=1024)
    ])
    external_photo_url = TextField('External Photo URL', [
        Optional(),
        Length(max=1024)
    ])
    country_id = IntegerField('Country ID', [Optional()])

# Define the create publisher form (WTForms)
class CreatePublisherForm(Form):
    name = TextField('Name', [
        InputRequired(message='You must provide a name.'),
        Length(max=128)
    ])
    description = TextField('Description', [
        Optional(),
        Length(max=256)
    ])
    country_id = IntegerField('Country ID', [Optional()])

# Define the update publisher form (WTForms)
class UpdatePublisherForm(Form):
    name = TextField('Name', [
        Optional(),
        Length(max=128)
    ])
    description = TextField('Description', [
        Optional(),
        Length(max=256)
    ])
    country_id = IntegerField('Country ID', [Optional()])

# Define the create genre form (WTForms)
class CreateGenreForm(Form):
    name = TextField('Name', [
        InputRequired(message='You must provide a name.'),
        Length(max=128)
    ])

# Define the update genre form (WTForms)
class UpdateGenreForm(Form):
    name = TextField('Name', [
        Optional(),
        Length(max=128)
    ])

# Define the create book form (WTForms)
class CreateBookForm(Form):
    title = TextField('Title', [
        InputRequired(message='You must provide a title.'),
        Length(max=512)
    ])
    description = TextField('Description', [
        Optional(),
        Length(max=1024)
    ])
    isbn = TextField('ISBN', [
        Optional(),
        Length(max=128)
    ])
    publication_date = DateField('Publication Date', [Optional()])
    tags = TextField('Tags', [
        Optional(),
        Length(max=1024)
    ])
    language = TextField('Language', [
        Optional(),
        Length(max=32)
    ])
    number_pages = IntegerField('Number of Pages', [Optional()])
    observations = TextField('Observations', [
        Optional(),
        Length(max=1024)
    ])
    edition = IntegerField('Edition', [Optional()])
    external_photo_url = TextField('External Photo URL', [
        Optional(),
        Length(max=1024)
    ])
    country_id = IntegerField('Country ID', [Optional()])
    author_id = IntegerField('Author ID', [
        InputRequired(message='You must provide the author ID.'),
    ])
    publisher_id = IntegerField('Publisher ID', [Optional()])

# Define the update book form (WTForms)
class UpdateBookForm(Form):
    title = TextField('Title', [
        Optional(),
        Length(max=512)
    ])
    description = TextField('Description', [
        Optional(),
        Length(max=1024)
    ])
    isbn = TextField('ISBN', [
        Optional(),
        Length(max=128)
    ])
    publication_date = DateField('Publication Date', [Optional()])
    tags = TextField('Tags', [
        Optional(),
        Length(max=1024)
    ])
    language = TextField('Language', [
        Optional(),
        Length(max=32)
    ])
    number_pages = IntegerField('Number of Pages', [Optional()])
    observations = TextField('Observations', [
        Optional(),
        Length(max=1024)
    ])
    edition = IntegerField('Edition', [Optional()])
    external_photo_url = TextField('External Photo URL', [
        Optional(),
        Length(max=1024)
    ])
    country_id = IntegerField('Country ID', [Optional()])
    author_id = IntegerField('Author ID', [Optional()])
    publisher_id = IntegerField('Publisher ID', [Optional()])
