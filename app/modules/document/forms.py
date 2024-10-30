"""Validation forms for the documents module."""

from wtforms import Form
import wtforms_json
from wtforms import TextField, RadioField, IntegerField
from wtforms.validators import InputRequired, Email, Optional, Length

from app.modules.utils import DateField

wtforms_json.init()


class CreateDocumentCategoryForm(Form):
    code = TextField(
        "Code", [InputRequired(message="You must provide a code."), Length(max=128)]
    )
    name = TextField(
        "Name", [InputRequired(message="You must provide a name."), Length(max=256)]
    )


class UpdateDocumentCategoryForm(Form):
    code = TextField("Code", [Optional(), Length(max=128)])
    name = TextField("Name", [Optional(), Length(max=256)])


class CreateDocumentForm(Form):
    code = TextField("Code", [Optional(), Length(max=128)])
    description = TextField(
        "Description",
        [InputRequired(message="You must provide a description."), Length(max=256)],
    )
    observations = TextField("Observations", [Optional(), Length(max=512)])
    expires_at = DateField("Expires At", [Optional()])
    alert_email = TextField("Email Address", [Optional(), Email()])
    alert = RadioField(
        "Email Alert",
        choices=[(1, "Yes"), (0, "No")],
        validators=[
            InputRequired(
                "You must inform if an email alert is InputRequired: 1 (yes) or 0 (no)"
            )
        ],
    )
    days_to_alert = IntegerField("Days to Alert", [Optional()])
    document_category_id = IntegerField("Document Category ID", [Optional()])


class UpdateDocumentForm(Form):
    code = TextField("Code", [Optional(), Length(max=128)])
    description = TextField("Description", [Optional(), Length(max=256)])
    observations = TextField("Observations", [Optional(), Length(max=512)])
    expires_at = DateField("Expires At", [Optional()])
    alert_email = TextField("Email Address", [Email(), Optional(), Length(max=1024)])
    alert = RadioField(
        "Email Alert", choices=[(1, "Yes"), (0, "No")], validators=[Optional()]
    )
    days_to_alert = IntegerField("Days to Alert", [Optional()])
    document_category_id = IntegerField("Document Category ID", [Optional()])


class CreateDocumentModelForm(Form):
    # TODO: must be updated if other models should be allowed
    model_name = RadioField(
        "Model Name",
        choices=[
            ("User", "User"),
        ],
        validators=[InputRequired(message="You must provide a valid model name")],
    )
    model_id = IntegerField(
        "Model ID", [InputRequired(message="You must provide the model ID.")]
    )
    document_id = IntegerField(
        "Document ID", [InputRequired(message="You must provide the document ID.")]
    )


class CreateDocumentSharingForm(Form):
    shared_user_id = IntegerField(
        "Shared User ID",
        [InputRequired(message="You must provide the shared user ID.")],
    )
