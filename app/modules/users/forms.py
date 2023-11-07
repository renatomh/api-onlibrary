# -*- coding: utf-8 -*-

# Import Form
from wtforms import Form

# Import JSON extension for forms
import wtforms_json

# Import Form elements such as TextField and BooleanField (optional)
from wtforms import (
    TextField,
    RadioField,
    IntegerField,
    PasswordField,
    FieldList,
)  # BooleanField

# Import Form validators
from wtforms.validators import InputRequired, Email, EqualTo, Optional, Length

# Initiating JSON for forms
wtforms_json.init()


# Define the login form (WTForms)
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


# Define the register form (WTForms)
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


# Define the register form (WTForms)
class ForgotPasswordForm(Form):
    email = TextField(
        "Email Address",
        [
            Email(),
            InputRequired(message="You must provide an email address."),
            Length(max=128),
        ],
    )


# Define the reset password form (WTForms)
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


# Define the verification email address form (WTForms)
class VerifyEmailAddressForm(Form):
    token = TextField("Token", [InputRequired(message="You must provide a token.")])


# Define the status change form (WTForms)
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


# Define the set user FCM token form (WTForms)
class SetUserFCMTokenForm(Form):
    fcm_token = TextField(
        "FCM Token",
        [InputRequired(message="You must provide the FCM token."), Length(max=512)],
    )


# Define the set user SocketIO SID form (WTForms)
class SetUserSIDForm(Form):
    socketio_sid = TextField(
        "SocketIO SID",
        [InputRequired(message="You must provide the SocketIO SID."), Length(max=512)],
    )


# Define the create user form (WTForms)
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


# Define the user role form (WTForms)
class UserRoleForm(Form):
    role_id = IntegerField(
        "Role ID", [InputRequired(message="You must provide the role ID.")]
    )


# Define the update profile form (WTForms)
class UpdateProfileForm(Form):
    name = TextField("Name", [Optional(), Length(max=128)])
    username = TextField("Username", [Optional(), Length(max=128)])
    current_password = PasswordField("Current Password", [Optional()])
    new_password = PasswordField("New Password", [Optional()])
    password_confirmation = PasswordField("Password Confirmation", [Optional()])


# Define the update user form (WTForms)
class UpdateUserForm(Form):
    name = TextField("Name", [Optional(), Length(max=128)])
    username = TextField("Username", [Optional(), Length(max=128)])
    role_id = IntegerField("Role ID", [Optional()])
    password = PasswordField("New Password", [Optional()])
    password_confirmation = PasswordField("Password Confirmation", [Optional()])


# Define the create role form (WTForms)
class CreateRoleForm(Form):
    name = TextField(
        "Name", [InputRequired(message="You must provide a name."), Length(max=128)]
    )


# Define the update role form (WTForms)
class UpdateRoleForm(Form):
    name = TextField("Name", [Optional(), Length(max=128)])


# Define the create role API route form (WTForms)
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


# Define the create role web action form (WTForms)
class CreateRoleWebActionForm(Form):
    action = TextField(
        "Action",
        [InputRequired(message="You must provide an action."), Length(max=512)],
    )
    role_id = IntegerField(
        "Role ID", [InputRequired(message="You must provide the role ID.")]
    )


# Define the create role mobile action form (WTForms)
class CreateRoleMobileActionForm(Form):
    action = TextField(
        "Action",
        [InputRequired(message="You must provide an action."), Length(max=512)],
    )
    role_id = IntegerField(
        "Role ID", [InputRequired(message="You must provide the role ID.")]
    )


# Define the copy role form (WTForms)
class CopyRoleForm(Form):
    name = TextField("Name", [Optional(), Length(max=128)])
