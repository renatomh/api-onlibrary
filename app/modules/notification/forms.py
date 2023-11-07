# -*- coding: utf-8 -*-

# Import Form
from wtforms import Form

# Import JSON extension for forms
import wtforms_json

# Import Form elements such as TextField and BooleanField (optional)
from wtforms import TextField, RadioField, IntegerField

# Import Form validators
from wtforms.validators import InputRequired, Optional, Length
from app.modules.utils import DateTimeField

# Initiating JSON for forms
wtforms_json.init()


# Define the create notificaation form (WTForms)
class CreateNotificationForm(Form):
    title = TextField(
        "Title", [InputRequired(message="You must provide a title."), Length(max=128)]
    )
    description = TextField(
        "Description",
        [InputRequired(message="You must provide a description."), Length(max=1024)],
    )
    web_action = TextField("Web Action", [Optional(), Length(max=512)])
    mobile_action = TextField("Mobile Action", [Optional(), Length(max=512)])
    user_id = IntegerField(
        "User ID", [InputRequired(message="You must provide the user ID.")]
    )


# Define the update notification form (WTForms)
class UpdateNotificationForm(Form):
    title = TextField("Title", [Optional(), Length(max=128)])
    description = TextField("Description", [Optional(), Length(max=1024)])
    web_action = TextField("Web Action", [Optional(), Length(max=512)])
    mobile_action = TextField("Mobile Action", [Optional(), Length(max=512)])


# Define the read notification form (WTForms)
class ReadNotificationForm(Form):
    is_read = RadioField(
        "Is Read",
        choices=[(1, "Read"), (0, "Unread")],
        validators=[
            InputRequired(
                message="You must inform if notification is read: 1 (read) or 0 (unread)."
            )
        ],
    )
    read_at = DateTimeField(
        "Read At", format="%Y-%m-%dT%H:%M:%S%z", validators=[Optional()]
    )
