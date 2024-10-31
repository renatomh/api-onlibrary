"""Validation forms for the commons module."""

from wtforms import Form
import wtforms_json
from wtforms import TextField, IntegerField
from wtforms.validators import InputRequired, Optional, Length

wtforms_json.init()


class CreateUFForm(Form):
    code = TextField(
        "Code", [InputRequired(message="You must provide a code."), Length(max=128)]
    )
    name = TextField(
        "Name", [InputRequired(message="You must provide a name."), Length(max=128)]
    )


class UpdateUFForm(Form):
    code = TextField("Code", [Optional(), Length(max=128)])
    name = TextField("Name", [Optional(), Length(max=128)])


class CreateCityForm(Form):
    name = TextField(
        "Name", [InputRequired(message="You must provide a name."), Length(max=128)]
    )
    uf_id = IntegerField(
        "UF ID", [InputRequired(message="You must provide the UF ID.")]
    )


class UpdateCityForm(Form):
    name = TextField("Name", [Optional(), Length(max=128)])
    uf_id = IntegerField("UF ID", [Optional()])
