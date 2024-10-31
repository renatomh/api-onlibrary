"""Validation forms for the users module."""

from wtforms import Form
import wtforms_json
from wtforms import TextField, RadioField, IntegerField, PasswordField
from wtforms.validators import InputRequired, Email, EqualTo, Optional, Length

wtforms_json.init()


class LoginForm(Form):
    username = TextField(
        "Email Address/Username",
        [
            InputRequired(message="You must provide an email address or username."),
            Length(max=128),
        ],
    )
    password = PasswordField(
        "Password", [InputRequired(message="You must provide a password.")]
    )


class RegisterForm(Form):
    name = TextField(
        "Name", [InputRequired(message="You must provide a name."), Length(max=128)]
    )
    email = TextField(
        "Email Address",
        [
            Email(),
            InputRequired(message="You must provide an email address."),
            Length(max=128),
        ],
    )
    password = PasswordField(
        "Password",
        [
            EqualTo("password_confirmation", message="Passwords must match"),
            InputRequired(message="You must provide a password."),
        ],
    )
    password_confirmation = PasswordField(
        "Password Confirmation",
        [InputRequired(message="You must provide the password confirmation.")],
    )


class ForgotPasswordForm(Form):
    email = TextField(
        "Email Address",
        [
            Email(),
            InputRequired(message="You must provide an email address."),
            Length(max=128),
        ],
    )


class ResetPasswordForm(Form):
    reset_token = TextField(
        "Reset Token", [InputRequired(message="You must provide the reset token.")]
    )
    password = PasswordField(
        "Password",
        [
            EqualTo("password_confirmation", message="Passwords must match"),
            InputRequired(message="You must provide a password."),
        ],
    )
    password_confirmation = PasswordField(
        "Password Confirmation",
        [InputRequired(message="You must provide the password confirmation.")],
    )


class VerifyEmailAddressForm(Form):
    token = TextField("Token", [InputRequired(message="You must provide a token.")])


class SetIsActiveForm(Form):
    is_active = RadioField(
        "Is Active",
        choices=[(1, "Active"), (0, "Inactive")],
        validators=[
            InputRequired(
                message="You must inform the current status: 1 (active) or 0 (inactive)"
            )
        ],
    )


class SetUserFCMTokenForm(Form):
    fcm_token = TextField(
        "FCM Token",
        [InputRequired(message="You must provide the FCM token."), Length(max=512)],
    )


class SetUserSIDForm(Form):
    socketio_sid = TextField(
        "SocketIO SID",
        [InputRequired(message="You must provide the SocketIO SID."), Length(max=512)],
    )


class CreateUserForm(Form):
    name = TextField(
        "Name", [InputRequired(message="You must provide a name."), Length(max=128)]
    )
    username = TextField(
        "Username",
        [InputRequired(message="You must provide the username"), Length(max=128)],
    )
    password = PasswordField(
        "Password",
        [
            EqualTo("password_confirmation", message="Passwords must match"),
            InputRequired(message="You must provide a password."),
        ],
    )
    password_confirmation = PasswordField(
        "Password Confirmation",
        [InputRequired(message="You must provide the password confirmation.")],
    )
    role_id = IntegerField(
        "Role ID", [InputRequired(message="You must provide the role ID.")]
    )
    is_active = RadioField(
        "Is Active",
        choices=[(1, "Active"), (0, "Inactive")],
        validators=[
            InputRequired(
                message="You must inform the current status: 1 (active) or 0 (inactive)"
            )
        ],
    )
    email = TextField("Email Address", [Email(), Optional(), Length(max=128)])


class UserRoleForm(Form):
    role_id = IntegerField(
        "Role ID", [InputRequired(message="You must provide the role ID.")]
    )


class UpdateProfileForm(Form):
    name = TextField("Name", [Optional(), Length(max=128)])
    username = TextField("Username", [Optional(), Length(max=128)])
    current_password = PasswordField("Current Password", [Optional()])
    new_password = PasswordField("New Password", [Optional()])
    password_confirmation = PasswordField("Password Confirmation", [Optional()])


class UpdateUserForm(Form):
    name = TextField("Name", [Optional(), Length(max=128)])
    username = TextField("Username", [Optional(), Length(max=128)])
    role_id = IntegerField("Role ID", [Optional()])
    password = PasswordField("New Password", [Optional()])
    password_confirmation = PasswordField("Password Confirmation", [Optional()])


class CreateRoleForm(Form):
    name = TextField(
        "Name", [InputRequired(message="You must provide a name."), Length(max=128)]
    )


class UpdateRoleForm(Form):
    name = TextField("Name", [Optional(), Length(max=128)])


class CreateRoleAPIRouteForm(Form):
    route = TextField(
        "Route", [InputRequired(message="You must provide a route."), Length(max=512)]
    )
    method = RadioField(
        "Method",
        choices=[
            ("GET", "GET"),
            ("POST", "POST"),
            ("PUT", "PUT"),
            ("PATCH", "PATCH"),
            ("DELETE", "DELETE"),
        ],
        validators=[
            InputRequired(
                message="You must provide the method (GET, POST, PUT, PATCH or DELETE)."
            )
        ],
    )
    role_id = IntegerField(
        "Role ID", [InputRequired(message="You must provide the role ID.")]
    )


class CreateRoleWebActionForm(Form):
    action = TextField(
        "Action",
        [InputRequired(message="You must provide an action."), Length(max=512)],
    )
    role_id = IntegerField(
        "Role ID", [InputRequired(message="You must provide the role ID.")]
    )


class CreateRoleMobileActionForm(Form):
    action = TextField(
        "Action",
        [InputRequired(message="You must provide an action."), Length(max=512)],
    )
    role_id = IntegerField(
        "Role ID", [InputRequired(message="You must provide the role ID.")]
    )


class CopyRoleForm(Form):
    name = TextField("Name", [Optional(), Length(max=128)])
