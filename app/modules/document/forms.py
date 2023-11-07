# -*- coding: utf-8 -*-

# Import Form
from wtforms import Form

# Import JSON extension for forms
import wtforms_json

# Import Form elements such as TextField and BooleanField (optional)
from wtforms import TextField, RadioField, IntegerField

# Import Form validators
from wtforms.validators import InputRequired, Email, Optional, Length
from app.modules.utils import DateField

# Initiating JSON for forms
wtforms_json.init()


# Define the create document category form (WTForms)
class CreateDocumentCategoryForm(Form):
    code = TextField(
        "Code", [InputRequired(message="You must provide a code."), Length(max=128)]
    )
    name = TextField(
        "Name", [InputRequired(message="You must provide a name."), Length(max=256)]
    )


# Define the update document category form (WTForms)
class UpdateDocumentCategoryForm(Form):
    code = TextField("Code", [Optional(), Length(max=128)])
    name = TextField("Name", [Optional(), Length(max=256)])


# Define the create document form (WTForms)
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


# Define the update document form (WTForms)
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


# Define the create document model form (WTForms)
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


# Define the create document sharing form (WTForms)
class CreateDocumentSharingForm(Form):
    shared_user_id = IntegerField(
        "Shared User ID",
        [InputRequired(message="You must provide the shared user ID.")],
    )
