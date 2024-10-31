"""Validation forms for the logs module."""

from wtforms import Form
import wtforms_json
from wtforms import TextField, RadioField, IntegerField
from wtforms.validators import InputRequired, Length

wtforms_json.init()


class CreateLogForm(Form):
    model_name = RadioField(
        "Model Name",
        # TODO: must be updated if other models should be allowed
        choices=[
            ("User", "User"),
        ],
        validators=[InputRequired(message="You must provide a valid model name")],
    )
    description = TextField(
        "Description",
        [InputRequired(message="You must provide a description."), Length(max=1024)],
    )
    model_id = IntegerField(
        "Model ID", [InputRequired(message="You must provide the model ID.")]
    )
