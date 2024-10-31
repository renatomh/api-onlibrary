"""Validation forms for the notifications module."""

from wtforms import Form
import wtforms_json
from wtforms import TextField, RadioField, IntegerField
from wtforms.validators import InputRequired, Optional, Length

from app.modules.utils import DateTimeField

wtforms_json.init()


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


class UpdateNotificationForm(Form):
    title = TextField("Title", [Optional(), Length(max=128)])
    description = TextField("Description", [Optional(), Length(max=1024)])
    web_action = TextField("Web Action", [Optional(), Length(max=512)])
    mobile_action = TextField("Mobile Action", [Optional(), Length(max=512)])


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
