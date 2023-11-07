# -*- coding: utf-8 -*-

# Import Form
from wtforms import Form

# Import JSON extension for forms
import wtforms_json

# Import Form elements such as TextField and BooleanField (optional)
from wtforms import TextField, RadioField, IntegerField, FloatField  # BooleanField

# Import Form validators
from wtforms.validators import InputRequired, Optional, Length
from app.modules.utils import DateField

# Initiating JSON for forms
wtforms_json.init()


# Define the create UF form (WTForms)
class CreateUFForm(Form):
    code = TextField(
        "Code", [InputRequired(message="You must provide a code."), Length(max=128)]
    )
    name = TextField(
        "Name", [InputRequired(message="You must provide a name."), Length(max=128)]
    )


# Define the update UF form (WTForms)
class UpdateUFForm(Form):
    code = TextField("Code", [Optional(), Length(max=128)])
    name = TextField("Name", [Optional(), Length(max=128)])


# Define the create city form (WTForms)
class CreateCityForm(Form):
    name = TextField(
        "Name", [InputRequired(message="You must provide a name."), Length(max=128)]
    )
    uf_id = IntegerField(
        "UF ID", [InputRequired(message="You must provide the UF ID.")]
    )


# Define the update city form (WTForms)
class UpdateCityForm(Form):
    name = TextField("Name", [Optional(), Length(max=128)])
    uf_id = IntegerField("UF ID", [Optional()])
