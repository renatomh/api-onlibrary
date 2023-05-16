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
