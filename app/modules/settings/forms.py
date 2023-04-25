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

# Define the create library form (WTForms)
class CreateLibraryForm(Form):
    name = TextField('Name', [
        InputRequired(message='You must provide a name.'),
        Length(max=128)
    ])

    # Identification Data: email, password, etc.
    cnpj = TextField('CNPJ', [
        Optional(),
        Length(max=18)
    ])
    cpf = TextField('CPF', [
        Optional(),
        Length(max=18)
    ])
    city_id = IntegerField('City ID', [Optional()])

# Define the update library form (WTForms)
class UpdateLibraryForm(Form):
    name = TextField('Name', [
        Optional(),
        Length(max=128)
    ])

    # Identification Data: email, password, etc.
    cnpj = TextField('CNPJ', [
        Optional(),
        Length(max=18)
    ])
    cpf = TextField('CPF', [
        Optional(),
        Length(max=18)
    ])
    city_id = IntegerField('City ID', [Optional()])

# Define the create city form (WTForms)
class CreateCityForm(Form):
    name = TextField('Name', [
        InputRequired(message='You must provide a name.'),
        Length(max=128)
    ])
    uf = TextField('UF', [
        InputRequired(message='You must provide a UF.'),
        Length(max=16)
    ])
    country_id = IntegerField('Country ID', [
        InputRequired(message='You must provide the country ID.')
    ])

# Define the update city form (WTForms)
class UpdateCityForm(Form):
    name = TextField('Name', [
        Optional(),
        Length(max=128)
    ])
    uf = TextField('UF', [
        Optional(),
        Length(max=16)
    ])
    country_id = IntegerField('Coutry ID', [Optional()])

# Define the create country form (WTForms)
class CreateCountryForm(Form):
    name = TextField('Name', [
        InputRequired(message='You must provide a name.'),
        Length(max=128)
    ])
    code = TextField('Code', [
        InputRequired(message='You must provide a code.'),
        Length(max=8)
    ])

# Define the update country form (WTForms)
class UpdateCountryForm(Form):
    name = TextField('Name', [
        Optional(),
        Length(max=128)
    ])
    code = TextField('Code', [
        Optional(),
        Length(max=8)
    ])
