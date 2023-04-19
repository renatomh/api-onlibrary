# -*- coding: utf-8 -*-

# Import Form
from wtforms import Form

# Import JSON extension for forms
import wtforms_json

# Import Form elements such as TextField and BooleanField (optional)
from wtforms import TextField, RadioField, IntegerField

# Import Form validators
from wtforms.validators import InputRequired, Length

# Initiating JSON for forms
wtforms_json.init()

# Define the create log form (WTForms)
class CreateLogForm(Form):
    # TODO: must be updated if other models should be allowed
    model_name = RadioField('Model Name', 
        choices=[
            ('User', 'User'),
        ],
        validators=[
            InputRequired(message='You must provide a valid model name')
        ]
    )
    description = TextField('Description', [
        InputRequired(message='You must provide a description.'),
        Length(max=1024)
    ])
    model_id = IntegerField('Model ID', [
        InputRequired(message='You must provide the model ID.')
    ])
