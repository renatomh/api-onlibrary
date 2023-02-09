# -*- coding: utf-8 -*-
"""
Refs:
    * Flask Request Documentation: https://tedboy.github.io/flask/generated/generated/flask.Request.html
    * SQLAlchemy Operator Reference: https://docs.sqlalchemy.org/en/14/core/operators.html
    
"""

# Import flask dependencies
from os import path, environ
from flask import Blueprint, request, jsonify, g, \
    render_template
from flask_babel import _

# Function to be called on 'eval', in order to join models relationships
from sqlalchemy.orm import selectinload #, noload

# Import password / encryption helper tools
from werkzeug.security import check_password_hash, generate_password_hash

# Session maker to allow database communication
from app import AppSession
# SocketIO communication
from app import socketio

# Function for files upload
from werkzeug.utils import secure_filename
# Library to get current timestamp
import time
# Import services
from app.services.storage import store_file, remove_file
from app.services.mail import send_mail
from app.services.thumbnail import get_image_thumbnail
# Config variables
from config import UPLOAD_TEMP_FOLDER, ALLOWED_IMAGE_EXTENSIONS, \
    ALLOWED_EMAIL_DOMAINS, tz

# Module for regular expressions
import re

# Import dependencies
import pytz
from datetime import datetime

# Middlewares
from app.middleware import ensure_authenticated, ensure_authorized

# Import module forms
from app.modules.users.forms import *

# Import module models
from app.modules.users.models import *
from app.modules.notification.models import *
from app.modules.log.models import *

# Utilities functions
from app.modules.utils import get_sort_attrs, get_join_attrs, \
    get_filter_attrs

# Define the blueprint: 'auth', set its url prefix: app.url/auth
mod_auth = Blueprint('auth', __name__, url_prefix='/auth')
mod_profile = Blueprint('profile', __name__, url_prefix='/profile')
mod_user = Blueprint('users', __name__, url_prefix='/users')
mod_role = Blueprint('roles', __name__, url_prefix='/roles')
mod_role_api_route = Blueprint('role_api_routes', __name__, url_prefix='/role_api_routes')
mod_role_web_action = Blueprint('role_web_actions', __name__, url_prefix='/role_web_actions')
mod_role_mobile_action = Blueprint('role_mobile_actions', __name__, url_prefix='/role_mobile_actions')

# Set the route and accepted methods
@mod_auth.route('/login', methods=['POST'])
def login():
    # For POST method
    if request.method == 'POST':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = LoginForm.from_json(request.json)

            # Validating provided data
            if form.validate():
                # Defining regex to check if string contains valid email address
                email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                # Checking if an email address or username was provided
                if(re.fullmatch(email_regex, form.username.data)):
                    # Searching user by email address
                    user = session.query(User).filter(
                        User.email == form.username.data).first()
                else:
                    # Searching user by username
                    user = session.query(User).filter(
                        User.username == form.username.data).first()

                # If user is found and passwords match
                if user and check_password_hash(user.hashpass, form.password.data):
                    # Is user is not active
                    if user.is_active == 0:
                        return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("Account not active. Please contact the system admin.")}}), 401

                    # Updating the last login date on the user object
                    user.last_login_at = datetime.now(tz)

                    # Getting model and relationships data
                    data = user.as_dict()
                    data['role'] = user.role.as_dict() if user.role else None
                    # Getting role web and mobile actions
                    role_web_actions = session.query(RoleWebAction).filter_by(role_id=user.role_id).all()
                    role_mobile_actions = session.query(RoleMobileAction).filter_by(role_id=user.role_id).all()
                    data['role']['web_actions'] = [d.action for d in role_web_actions]
                    data['role']['mobile_actions'] = [d.action for d in role_mobile_actions]
                    # Getting the unread notifications count for the user
                    data['unread_notifications_count'] = session.query(Notification).filter_by(
                            user_id=user.id,
                            is_read=0,
                        ).count()

                    # Checking if a user agent was provided on the headers
                    if ('User-Agent' in request.headers.keys()):
                        # Cropping for really long strings
                        user_agent = request.headers['User-Agent'][:750]
                    # If it wasn't provided
                    else: user_agent = _('Not provided')

                    # Creating log for user's login
                    log_item = Log(
                        model_name='User',
                        ip_address=request.environ.get('HTTP_X_REAL_IP', request.remote_addr),
                        description=f"{_('User has logged in.')} (User-Agent: {user_agent})",
                        model_id=user.id,
                        user_id=user.id,
                        )
                    session.add(log_item)
                    # Flushing and comitting the changes
                    session.flush()
                    session.commit()
                    # Generating the JWT and returning data
                    data['token'] = user.encode_auth_token(user.id)
                    return jsonify({"data": data,
                                    "meta": {"success": True}})

                # If no user is found or passwords don't match
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("User/password combination doesn't match.")}}), 401

            # If something goes wrong
            else:
                # Returning the data to the request
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": form.errors}}), 400

# Socket.IO eevent listener for when client set user's SID
@socketio.on("set-user-token")
def set_user_token(data):
    # Info about data sent
    print(f"Setting client (SID: {request.sid}) user token {data}")
    
    # If no user token was provided, we just ignore and return
    if not 'user_token' in data.keys(): return

    # Otherwise, we check if user token is valid
    user_id = User.decode_auth_token(data['user_token'])

    # If token is not valid, we'll also ignore and return
    if type(user_id) is not int: return

    # Creating the session for database communication
    with AppSession() as session:
        # If token is valid, we'll search the user by ID
        user = session.query(User).get(user_id)
        # If no user is found, once again, we ignore and return
        if user is None: return
        # Otherwise, we'll set the Socket.IO session ID to the user
        user.socketio_sid = request.sid
        # Flushing and comitting the changes
        session.flush()
        session.commit()

# Set the route and accepted methods
@mod_user.route('/<int:id>/fcm-token', methods=['PATCH'])
@ensure_authorized
def set_user_fcm_token(id):
    # For PATCH method
    if request.method == 'PATCH':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = SetUserFCMTokenForm.from_json(request.json)

            # Validating provided data
            if form.validate():
                # Updating the item
                item = session.query(User).get(id)
                if item:
                    # Setting the new FCM token for the user
                    item.fcm_token=form.fcm_token.data

                    try:
                        session.commit()
                        # Getting model and relationships data
                        data = item.as_dict()
                        data['role'] = item.role.as_dict() if item.role else None
                        return jsonify({"data": data,
                                        "meta": {"success": True}})

                     # If an error occurrs
                    except Exception as e:
                        session.rollback()
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": str(e)}}), 500

                # If no item is found
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("No item found")}}), 404

            # If something goes wrong
            else:
                # Returning the data to the request
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": form.errors}}), 400

# Set the route and accepted methods
@mod_user.route('/my/fcm-token', methods=['PATCH'])
@ensure_authenticated
def set_own_user_fcm_token():
    # For PATCH method
    if request.method == 'PATCH':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = SetUserFCMTokenForm.from_json(request.json)

            # Validating provided data
            if form.validate():
                # Updating the item
                item = session.query(User).get(g.user.id)
                if item:
                    # Setting the new FCM token for the user
                    item.fcm_token=form.fcm_token.data

                    try:
                        session.commit()
                        # Getting model and relationships data
                        data = item.as_dict()
                        data['role'] = item.role.as_dict() if item.role else None
                        return jsonify({"data": data,
                                        "meta": {"success": True}})

                    # If an error occurrs
                    except Exception as e:
                        session.rollback()
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": str(e)}}), 500

                # If no item is found
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("No item found")}}), 404

            # If something goes wrong
            else:
                # Returning the data to the request
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": form.errors}}), 400

# Set the route and accepted methods
@mod_auth.route('/register', methods=['POST'])
def register():
    # For POST method
    if request.method == 'POST':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = RegisterForm.from_json(request.json)

            # Validating provided data
            if form.validate():
                # Searching user by email address
                user = session.query(User).filter_by(email=form.email.data).first()
                
                # If a user is found, returns information about the error
                if user:
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": _("This email address is "
                                            "already registered.")}}), 409

                # Flag to generate a new username from the email address
                is_username_valid = False
                # Initializing data to set username
                email_username = form.email.data.split('@')[0]
                username = email_username
                sequential = 1
                # While a valid username couldn't be obtained
                while (not is_username_valid):
                    # Searching user by username generated from email
                    user = session.query(User).filter_by(username=username).first()
                    # If a user is found, we try the next sequential
                    if user:
                        username = f"{email_username}{str(sequential)}"
                        sequential += 1
                    # If no user is found, the new username is valid
                    else:
                        is_username_valid = True

                # We also check if the email address domain is allowed
                if form.email.data.split('@')[1] not in ALLOWED_EMAIL_DOMAINS and \
                    '*' not in ALLOWED_EMAIL_DOMAINS:
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": _("This email domain is "
                                            "not allowed.")}}), 400
                
                # For the library ID, it could be mapped according to the e-mail domain
                # TODO: define how to select the user's library ID on register
                library_id = None

                # Creating new user
                user = User(
                    name=form.name.data,
                    email=form.email.data,
                    username=username,
                    hashpass=generate_password_hash(form.password.data),
                    library_id=library_id,
                    )
                session.add(user)
                session.flush()
                session.commit()
                verif_token = user.encode_verif_token(user.id)

                # Creating verification email
                # Replacing data on template
                body_html = render_template('emails/verify_email.html', **{
                    'name': user.name,
                    'link': f"{environ.get('APP_WEB_URL')}/verify-email?token={verif_token}",
                })

                # Sending confirmation mail
                send_mail(
                    recipients=[form.email.data],
                    subject=_('Welcome to OnLibrary!'),
                    body_html=body_html,
                    sender='Postmaster | OnLibrary'
                    )

                return jsonify({"data": user.as_dict(),
                                "meta": {"success": True}})
            
            # If something goes wrong
            else:
                # Returning the data to the request
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": form.errors}}), 400

# Set the route and accepted methods
@mod_auth.route('/forgot-password', methods=['PUT'])
def forgot_password():
    # For PUT method
    if request.method == 'PUT':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = ForgotPasswordForm.from_json(request.json)

            # Validating provided data
            if form.validate():
                # Searching user by email address
                user = session.query(User).filter_by(email=form.email.data).first()
                
                # If no user is found, we inform the error
                if user is None:
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": _("This email address is "
                                            "not registered.")}}), 404

                # Creating the reset password token
                reset_token = user.encode_auth_token(user.id)

                # Creating verification email
                # Replacing data on template
                body_html = render_template('emails/forgot_password.html', **{
                    'name': user.name,
                    'link': f"{environ.get('APP_WEB_URL')}/reset-password?reset_token={reset_token}",
                })

                # Sending confirmation mail
                send_mail(
                    recipients=[form.email.data],
                    subject=_('OnLibrary Password Reset'),
                    body_html=body_html,
                    sender='Postmaster | OnLibrary'
                    )

                return jsonify({"data": user.as_dict(),
                                "meta": {"success": True}})
            
            # If something goes wrong
            else:
                # Returning the data to the request
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": form.errors}}), 400

# Set the route and accepted methods
@mod_auth.route('/reset-password', methods=['PUT'])
def reset_password():
    # For PUT method
    if request.method == 'PUT':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = ResetPasswordForm.from_json(request.json)

            # Validating provided data
            if form.validate():
                res = User.decode_verif_token(form.reset_token.data)
                # If token is not valid
                if type(res) is not int:
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": res}}), 400
                # Updating the item
                user = session.query(User).get(res)
                if user:
                    user.hashpass=generate_password_hash(form.password.data)

                    try:
                        session.commit()
                        # Getting model and relationships data
                        data = user.as_dict()
                        data['role'] = user.role.as_dict() if user.role else None
                        return jsonify({"data": data,
                                        "meta": {"success": True}})

                    # If something goes wrong while committing
                    except Exception as e:
                        session.rollback()
                        # Returning the data to the request
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": str(e)}}), 500
                
                # If no item is found
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("No user found")}}), 404
            
            # If something goes wrong
            else:
                # Returning the data to the request
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": form.errors}}), 400

# Set the route and accepted methods
@mod_user.route('/verify', methods=['PUT'])
def verify_email_address():
    # For PUT method
    if request.method == 'PUT':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = VerifyEmailAddressForm.from_json(request.json)

            # Validating provided data
            if form.validate():
                res = User.decode_verif_token(form.token.data)
                # If token is not valid
                if type(res) is not int:
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": res}}), 400
                # Updating the item
                user = session.query(User).get(res)
                if user:
                    user.is_verified=1
                    user.is_active=1

                    try:
                        session.commit()
                        # Getting model and relationships data
                        data = user.as_dict()
                        data['role'] = user.role.as_dict() if user.role else None
                        return jsonify({"data": data,
                                        "meta": {"success": True}})

                    # If something goes wrong while committing
                    except Exception as e:
                        session.rollback()
                        # Returning the data to the request
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": str(e)}}), 500

                # If no item is found
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("No user found")}}), 404

            # If something goes wrong
            else:
                # Returning the data to the request
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": form.errors}}), 400

# Set the route and accepted methods
@mod_user.route('/<int:id>/is-active', methods=['PUT'])
@ensure_authorized
def activate_user(id):
    # For PUT method
    if request.method == 'PUT':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = SetIsActiveForm.from_json(request.json)

            # Validating provided data
            if form.validate():
                # Updating the item
                user = session.query(User).get(id)
                if user:
                    user.is_active=int(form.is_active.data)

                    try:
                        session.commit()
                        # Getting model and relationships data
                        data = user.as_dict()
                        data['role'] = user.role.as_dict() if user.role else None
                        return jsonify({"data": data,
                                        "meta": {"success": True}})

                    # If something goes wrong while committing
                    except Exception as e:
                        session.rollback()
                        # Returning the data to the request
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": str(e)}}), 500

                # If no item is found
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("No user found")}}), 404

            # If something goes wrong
            else:
                # Returning the data to the request
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": form.errors}}), 400

# Set the route and accepted methods
@mod_user.route('/<int:id>/role', methods=['PUT'])
@ensure_authorized
def change_user_role(id):
    # For PUT method
    if request.method == 'PUT':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = UserRoleForm.from_json(request.json)

            # Validating provided data
            if form.validate():
                # Updating the item
                user = session.query(User).get(id)
                if user:
                    # Checking if the user role exists
                    role = session.query(Role).get(form.role_id.data)
                    if role:
                        user.role_id=form.role_id.data

                        try:
                            session.commit()
                            # Getting model and relationships data
                            data = user.as_dict()
                            data['role'] = user.role.as_dict() if user.role else None
                            return jsonify({"data": data,
                                            "meta": {"success": True}})

                        # If something goes wrong while committing
                        except Exception as e:
                            session.rollback()
                            # Returning the data to the request
                            return jsonify({"data": [],
                                            "meta": {"success": False,
                                                    "errors": str(e)}}), 500

                    # If no item is found
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": _("No role found")}}), 404

                # If no item is found
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("No user found")}}), 404

            # If something goes wrong
            else:
                # Returning the data to the request
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": form.errors}}), 400

# Set the route and accepted methods
@mod_user.route('', methods=['GET'])
@ensure_authorized
def index_user():
    # For GET method
    if request.method == 'GET':
        # Pagination
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=25, type=int)
        # Setting up a maximum number of results per page, even if limit exceeds it
        max_per_page = 250
        # Filtering and sorting
        filter = request.args.get('filter', default='[]', type=str)
        sort = request.args.get('sort', default='[]', type=str)
        # Query timezone
        timezone = request.args.get('timezone', default=os.getenv('TZ', 'UTC'), type=str)
        try: q_tz = pytz.timezone(timezone)
        except: q_tz = pytz.timezone(os.getenv('TZ', 'UTC'))

        # Defining the class for the data model, must be updated for different models
        model = User
        # Getting the model relationships and evaluating the call string in order to load the relationships
        # TODO: if there is a better way to do this without 'eval', it should be used (https://realpython.com/python-eval-function/)
        # However, this shouldn't represent a risk, since the string being used can be trusted
        # We've tried creating 'tuples', 'maps', 'lists', etc. but kept getting the following error:
        # "mapper option expects string key or list of attributes"
        selectinloads = eval(''.join(f'selectinload({r}), ' for r in list(model.__mapper__.relationships)))
        # If we want to eager load the relationships' relationships as well, we can use the 'options' parameter like so:
        # .options(joinedload('*'))
        # We can also remove some relationships eager loading on the previous statement, like so:
        # .options(joinedload('*'), noload(User.children))

        # Trying to obtain data from models
        try:
            # Retrieving the sorting attributes
            sort_attrs = get_sort_attrs(model, sort)
            # Retrieving the join relationship models
            join_attrs = get_join_attrs(model, filter)
            # Retrieving the filtering attributes
            filter_attrs = get_filter_attrs(model, filter, q_tz)

            # Searching itens by filters and sorting
            if (len(join_attrs) > 0):
                # If joins are required
                res = model.query.options(selectinloads).join(*join_attrs).filter(
                    *filter_attrs).order_by(*sort_attrs).paginate(page, limit, False, max_per_page)
            else:
                # If joins are not required
                res = model.query.options(selectinloads).filter(*filter_attrs).order_by(
                    *sort_attrs).paginate(page, limit, False, max_per_page)

            # If we need to load specific relatonships's relationships, we can do something like follows
            # Though it might might lower performance for large sets
            # for r in res.items:
            #    r.role.children = Test.query.get(r.role.children_id)
            data = [r.as_dict(q_tz)
                    for r in res.items] if len(res.items) > 0 else []

            # Returning data and meta
            return jsonify({"data": data,
                            "meta": {"success": True,
                                     "count": res.total}})
        # If something goes wrong
        except Exception as e:
            return jsonify({"data": {},
                            "meta": {"success": False,
                                     "errors": str(e)}}), 500

# Set the route and accepted methods
@mod_user.route('', methods=['POST'])
@ensure_authorized
def create_user():
    # For POST method
    if request.method == 'POST':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = CreateUserForm.from_json(request.json)

            # Validating provided data
            if form.validate():
                # If an email was provided
                if form.email.data:
                    # Checking if email is already in use
                    if session.query(User).filter_by(email=form.email.data).first():
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": _("This email address is "
                                                "already registered.")}}), 409
                # Checking if username is already in use
                if session.query(User).filter_by(username=form.username.data).first():
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": _("This username is "
                                            "already in use.")}}), 409
                # Checking if role exists
                if session.query(Role).get(form.role_id.data) is None:
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": _("No role found")}}), 404

                try:
                    # Creating new user
                    user = User(
                        name=form.name.data,
                        username=form.username.data,
                        hashpass=generate_password_hash(form.password.data),
                        role_id=form.role_id.data,
                        library_id=g.user.library_id,
                        is_active=form.is_active.data,
                        email=form.email.data
                        )
                    session.add(user)
                    session.flush()
                    session.commit()
                    return jsonify({"data": user.as_dict(),
                                    "meta": {"success": True}})

                # If an error occurrs
                except Exception as e:
                    session.rollback()
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": str(e)}}), 500

            # If something goes wrong
            else:
                # Returning the data to the request
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": form.errors}}), 400

# Set the route and accepted methods
@mod_user.route('/<int:id>', methods=['GET'])
@ensure_authorized
def get_user_by_id(id):
    # For GET method
    if request.method == 'GET':
        # Creating the session for database communication
        with AppSession() as session:
            # Defining the class for the data model, must be updated for different models
            model = User
            selectinloads = eval(''.join(f'selectinload({r}), ' for r in list(model.__mapper__.relationships)))

            # Searching item by ID
            item = session.query(model).options(selectinloads).get(id)

            # If item is found
            if item:
                # Getting model and relationships data
                data = item.as_dict()

                # Returning the obtained data
                return jsonify({"data": data,
                                "meta": {"success": True}})

            # If no item is found
            return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("No item found")}}), 404

# Set the route and accepted methods
@mod_user.route('/<int:id>', methods=['PUT'])
@ensure_authorized
def update_user(id):
    # For PUT method
    if request.method == 'PUT':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = UpdateUserForm.from_json(request.json)

            # Validating provided data
            if form.validate():
                # Getting the user object
                user = session.query(User).get(id)

                # Updating the item
                if user:
                    if form.name.data is not None:
                        user.name=form.name.data
                    if form.username.data is not None:
                        # If the user tried to change its username
                        if form.username.data != user.username:
                            # Checking if username is not already in use
                            if session.query(User).filter_by(username=form.username.data).first():
                                return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": _("This username is already in use.")}}), 409
                            else:
                                user.username=form.username.data
                    if form.role_id.data is not None:
                        # Checking if role exists
                        if session.query(Role).get(form.role_id.data) is None:
                            return jsonify({"data": [],
                                            "meta": {"success": False,
                                                    "errors": _("No role found")}}), 404
                        else:
                            user.role_id=form.role_id.data

                    # If a new passowrd was provided, we also need the confirmation
                    if form.password.data is not None:
                        # The new password and the password confirmation must match
                        if form.password.data != form.password_confirmation.data:
                            return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("Passwords don't match.")}}), 400
                        # If everything is ok, we update the user's password
                        user.hashpass=generate_password_hash(form.password.data)

                    try:
                        session.commit()
                        # Getting model and relationships data
                        data = user.as_dict()
                        data['role'] = user.role.as_dict() if user.role else None
                        return jsonify({"data": data,
                                        "meta": {"success": True}})

                    # If something goes wrong while committing
                    except Exception as e:
                        session.rollback()
                        # Returning the data to the request
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": str(e)}}), 500

                # If no item is found
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("No user found")}}), 404
            
            # If something goes wrong
            else:
                # Returning the data to the request
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": form.errors}}), 400

# Set the route and accepted methods
@mod_user.route('/<int:id>', methods=['DELETE'])
@ensure_authorized
def delete_user(id):
    # For DELETE method
    if request.method == 'DELETE':
        # Creating the session for database communication
        with AppSession() as session:
            # Searching item by ID
            item = session.query(User).filter_by(id=id).first()

            # If the item is found
            if item:
                try:
                    # Here we might also have to remove the files from the server
                    # So we first retrieve the file URL
                    avatar_url = item.avatar_url
                    avatar_thumbnail_url = item.avatar_thumbnail_url
                    # Removing the item
                    session.delete(item)
                    session.commit()
                    # Removing the files
                    if avatar_url is not None: remove_file(avatar_url)
                    if avatar_thumbnail_url is not None: remove_file(avatar_thumbnail_url)
                    return jsonify({"data": '',
                                    "meta": {"success": True}}), 204

                # If an error occurrs
                except Exception as e:
                    session.rollback()
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": str(e)}}), 500
            
            # If no item is found
            return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("No user found")}}), 404

# Set the route and accepted methods
@mod_profile.route('', methods=['GET'])
@ensure_authenticated
def get_profile():
    # For GET method
    if request.method == 'GET':
        # Getting the user object
        user = g.user
        # If user is found
        if user:
            # Getting model and relationships data
            data = user.as_dict()
            # Getting the unread notifications count for the user
            data['unread_notifications_count'] = Notification.query.filter_by(
                    user_id=user.id,
                    is_read=0,
                ).count()

            return jsonify({"data": data,
                            "meta": {"success": True}})
        # If no user is found
        return jsonify({"data": [],
                        "meta": {"success": False,
                                    "errors": _("No user found")}}), 404

# Set the route and accepted methods
@mod_profile.route('/avatar', methods=['POST'])
@ensure_authenticated
def update_avatar():
    # For POST method
    if request.method == 'POST':
        # Creating the session for database communication
        with AppSession() as session:
            # If required, we can access the multipart/form-data like so:
            # form_data = dict(request.form)

            # Getting the user object
            user = session.query(User).get(g.user.id)

            # If user is found
            if user:
                # Removing the previous avatar and thumbnail (if present)
                if user.avatar_url is not None:
                    remove_file(user.avatar_url)
                if user.avatar_thumbnail_url is not None:
                    remove_file(user.avatar_thumbnail_url)

                file = request.files['avatar']
                # Setting filename with timestamp to create almost unique filename
                filename = f'{round(time.time()*1000)}-{secure_filename(file.filename)}'

                # Checking if file extension is allowed
                if ('.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS):
                    # Loading to the temp folder
                    file.save(path.join(UPLOAD_TEMP_FOLDER, filename))

                    # Generating image thumbnail
                    file_thumb = get_image_thumbnail(path.join(UPLOAD_TEMP_FOLDER, filename))
                    # If the thumbnail was successfully generated
                    if file_thumb is not None:
                        # We'll get the thumbnail filename
                        filename_thumb = path.basename(file_thumb)
                    # Otherwise, we'll set the thumbnail filename as None
                    else: filename_thumb = None

                    # Calling the function to upload file to selected directory/container
                    upload_response = store_file(
                        path.join(UPLOAD_TEMP_FOLDER, filename), filename)
                    # If there was an error, we return the upload response
                    if not upload_response['meta']['success']:
                        return jsonify(upload_response)

                    # If a thumbnail was created
                    if filename_thumb is not None:
                        # Calling the function to upload file thumbnail to selected directory/container
                        upload_response = store_file(file_thumb, filename_thumb)
                        # If there was an error, we return the upload response
                        if not upload_response['meta']['success']:
                            return jsonify(upload_response)

                    # Updating the user avatar and thumbnail
                    user.avatar_url = filename
                    user.avatar_thumbnail_url = filename_thumb
                    try:
                        session.commit()
                        # Getting model and relationships data
                        data = user.as_dict()
                        data['role'] = user.role.as_dict() if user.role else None
                        return jsonify({"data": data,
                                        "meta": {"success": True}})

                    # If something goes wrong while committing
                    except Exception as e:
                        session.rollback()
                        # Returning the data to the request
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": str(e)}}), 500

                # Otherwise, we inform about the error
                return jsonify({"data": {},
                                "meta": {"success": False,
                                        "errors": (_("File extension not allowed"), ALLOWED_IMAGE_EXTENSIONS)}}), 400

            # If no user is found
            return jsonify({"data": [],
                            "meta": {"success": False,
                                        "errors": _("No user found")}}), 404

# Set the route and accepted methods
@mod_profile.route('', methods=['PUT'])
@ensure_authenticated
def update_profile():
    # For PUT method
    if request.method == 'PUT':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = UpdateProfileForm.from_json(request.json)

            # Validating provided data
            if form.validate():
                # Getting the user object
                user = session.query(User).get(g.user.id)

                # Updating the item
                if user:
                    if form.name.data is not None:
                        user.name=form.name.data
                    if form.username.data is not None:
                        # If the user tried to change its username
                        if form.username.data != user.username:
                            # Checking if username is not already in use
                            if session.query(User).filter_by(username=form.username.data).first():
                                return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": _("This username is already in use.")}}), 409
                            else:
                                user.username=form.username.data

                    # If a new passowrd was provided, we also need the current and the confirmation
                    if form.new_password.data is not None:
                        # If the current password was not provided
                        if form.current_password.data is None:
                            return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("Please inform your current password.")}}), 400
                        # If the current password provided is wrong
                        if not check_password_hash(user.hashpass, form.current_password.data):
                            return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("The provided current password is wrong.")}}), 400
                        # The new password and the password confirmation must match
                        if form.new_password.data != form.password_confirmation.data:
                            return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("Passwords don't match.")}}), 400
                        # If everything is ok, we update the user's password
                        user.hashpass=generate_password_hash(form.new_password.data)

                    try:
                        session.commit()
                        # Getting model and relationships data
                        data = user.as_dict()
                        data['role'] = user.role.as_dict() if user.role else None
                        return jsonify({"data": data,
                                        "meta": {"success": True}})

                    # If something goes wrong while committing
                    except Exception as e:
                        session.rollback()
                        # Returning the data to the request
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": str(e)}}), 500

                # If no item is found
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("No user found")}}), 404

            # If something goes wrong
            else:
                # Returning the data to the request
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": form.errors}}), 400

# Set the route and accepted methods
@mod_role.route('', methods=['GET'])
@ensure_authorized
def index_role():
    # For GET method
    if request.method == 'GET':
        # Pagination
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=25, type=int)
        # Setting up a maximum number of results per page, even if limit exceeds it
        max_per_page = 250
        # Filtering and sorting
        filter = request.args.get('filter', default='[]', type=str)
        sort = request.args.get('sort', default='[]', type=str)
        # Query timezone
        timezone = request.args.get('timezone', default=os.getenv('TZ', 'UTC'), type=str)
        try: q_tz = pytz.timezone(timezone)
        except: q_tz = pytz.timezone(os.getenv('TZ', 'UTC'))

        # Defining the class for the data model, must be updated for different models
        model = Role
        selectinloads = eval(''.join(f'selectinload({r}), ' for r in list(model.__mapper__.relationships)))

        # Trying to obtain data from models
        try:
            # Retrieving the sorting attributes
            sort_attrs = get_sort_attrs(model, sort)
            # Retrieving the join relationship models
            join_attrs = get_join_attrs(model, filter)
            # Retrieving the filtering attributes
            filter_attrs = get_filter_attrs(model, filter, q_tz)

            # Searching itens by filters and sorting
            if (len(join_attrs) > 0):
                # If joins are required
                res = model.query.options(selectinloads).join(*join_attrs).filter(
                    *filter_attrs).order_by(*sort_attrs).paginate(page, limit, False, max_per_page)
            else:
                # If joins are not required
                res = model.query.options(selectinloads).filter(*filter_attrs).order_by(
                    *sort_attrs).paginate(page, limit, False, max_per_page)
            data = [r.as_dict(q_tz)
                    for r in res.items] if len(res.items) > 0 else []

            # Returning data and meta
            return jsonify({"data": data,
                            "meta": {"success": True,
                                     "count": res.total}})
        # If something goes wrong
        except Exception as e:
            return jsonify({"data": {},
                            "meta": {"success": False,
                                     "errors": str(e)}}), 500

# Set the route and accepted methods
@mod_role.route('', methods=['POST'])
@ensure_authorized
def create_role():
    # For POST method
    if request.method == 'POST':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = CreateRoleForm.from_json(request.json)

            # Validating provided data
            if form.validate():
                try:
                    # Creating new role
                    role = Role(
                        name=form.name.data,
                        )
                    session.add(role)
                    session.flush()
                    session.commit()
                    return jsonify({"data": role.as_dict(),
                                    "meta": {"success": True}})
                # If an error occurrs
                except Exception as e:
                    session.rollback()
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": str(e)}}), 500
            
            # If something goes wrong
            else:
                # Returning the data to the request
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": form.errors}}), 400

# Set the route and accepted methods
@mod_role.route('/<int:id>', methods=['GET'])
@ensure_authorized
def get_role_by_id(id):
    # For GET method
    if request.method == 'GET':
        # Creating the session for database communication
        with AppSession() as session:
            # Searching item by ID
            role = session.query(Role).get(id)

            # If item is found
            if role:
                return jsonify({"data": role.as_dict(),
                                "meta": {"success": True}})
            
            # If no item is found
            return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("No role found")}}), 404

# Set the route and accepted methods
@mod_role.route('/<int:id>', methods=['PUT'])
@ensure_authorized
def update_role(id):
    # For PUT method
    if request.method == 'PUT':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = UpdateRoleForm.from_json(request.json)

            # Validating provided data
            if form.validate():
                try:
                    # Updating the role
                    role = session.query(Role).get(id)
                    if role:
                        if form.name.data is not None:
                            role.name=form.name.data
                        
                        try:
                            session.commit()
                            return jsonify({"data": role.as_dict(),
                                            "meta": {"success": True}})

                        # If something goes wrong while committing
                        except Exception as e:
                            session.rollback()
                            # Returning the data to the request
                            return jsonify({"data": [],
                                            "meta": {"success": False,
                                                    "errors": str(e)}}), 500

                    # If no item is found
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": _("No role found")}}), 404

                # If an error occurrs
                except Exception as e:
                    session.rollback()
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": str(e)}}), 500

            # If something goes wrong
            else:
                # Returning the data to the request
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": form.errors}}), 400

# Set the route and accepted methods
@mod_role.route('/<int:id>/copy', methods=['POST'])
@ensure_authorized
def copy_role(id):
    # For POST method
    if request.method == 'POST':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = CopyRoleForm.from_json(request.json)

            # Validating provided data
            if form.validate():
                try:
                    # Getting the source role to be copied
                    original_role = Role.query.get(id)
                    # If no role was found
                    if original_role is None:
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                 "errors": _("No role found")}}), 400
                    # If a name was provided, we'll use it
                    if form.name.data is not None: name = form.name.data
                    # Otherwise, we'll set a updated name
                    else: name = original_role.name[:123] + " (2)"
                    # Creating new role
                    role = Role(name=name)
                    session.add(role)
                    # We flush in order to make the new role ID available
                    session.flush()
                    # Now, we'll query all the original role API routes, web and mobile actions
                    original_api_routes = RoleAPIRoute.query.filter(
                            RoleAPIRoute.role_id==id,
                        ).all()
                    original_web_actions = RoleWebAction.query.filter(
                            RoleWebAction.role_id==id,
                        ).all()
                    original_mobile_actions = RoleMobileAction.query.filter(
                            RoleMobileAction.role_id==id,
                        ).all()
                    # Copying the API routes to the new role
                    for original_api_route in original_api_routes:
                        api_route = RoleAPIRoute(
                            route=original_api_route.route,
                            method=original_api_route.method,
                            role_id=role.id,
                            )
                        session.add(api_route)
                    # Copying the web actions to the new role
                    for original_web_action in original_web_actions:
                        web_action = RoleWebAction(
                            action=original_web_action.action,
                            role_id=role.id,
                            )
                        session.add(web_action)
                    # Copying the mobile actions to the new role
                    for original_mobile_action in original_mobile_actions:
                        mobile_action = RoleMobileAction(
                            action=original_mobile_action.action,
                            role_id=role.id,
                            )
                        session.add(mobile_action)
                    # Comitting the changes
                    session.commit()
                    return jsonify({"data": role.as_dict(),
                                    "meta": {"success": True}})
                # If an error occurrs
                except Exception as e:
                    session.rollback()
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": str(e)}}), 500

            # If something goes wrong
            else:
                # Returning the data to the request
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": form.errors}}), 400

# Set the route and accepted methods
@mod_role.route('/<int:id>', methods=['DELETE'])
@ensure_authorized
def delete_role(id):
    # For DELETE method
    if request.method == 'DELETE':
        # Creating the session for database communication
        with AppSession() as session:
            # Searching item by ID
            item = session.query(Role).filter_by(id=id).first()

            # If the item is found
            if item:
                try:
                    session.delete(item)
                    session.commit()
                    return jsonify({"data": '',
                                    "meta": {"success": True}}), 204
                # If an error occurrs
                except Exception as e:
                    session.rollback()
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": str(e)}}), 500
            
            # If no item is found
            return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("No role found")}}), 404

# Set the route and accepted methods
@mod_role_api_route.route('', methods=['GET'])
@ensure_authorized
def index_role_api_route():
    # For GET method
    if request.method == 'GET':
        # Pagination
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=25, type=int)
        # Setting up a maximum number of results per page, even if limit exceeds it
        max_per_page = 250
        # Filtering and sorting
        filter = request.args.get('filter', default='[]', type=str)
        sort = request.args.get('sort', default='[]', type=str)
        # Query timezone
        timezone = request.args.get('timezone', default=os.getenv('TZ', 'UTC'), type=str)
        try: q_tz = pytz.timezone(timezone)
        except: q_tz = pytz.timezone(os.getenv('TZ', 'UTC'))

        # Defining the class for the data model, must be updated for different models
        model = RoleAPIRoute
        selectinloads = eval(''.join(f'selectinload({r}), ' for r in list(model.__mapper__.relationships)))

        # Trying to obtain data from models
        try:
            # Retrieving the sorting attributes
            sort_attrs = get_sort_attrs(model, sort)
            # Retrieving the join relationship models
            join_attrs = get_join_attrs(model, filter)
            # Retrieving the filtering attributes
            filter_attrs = get_filter_attrs(model, filter, q_tz)

            # Searching itens by filters and sorting
            if (len(join_attrs) > 0):
                # If joins are required
                res = model.query.options(selectinloads).join(*join_attrs).filter(
                    *filter_attrs).order_by(*sort_attrs).paginate(page, limit, False, max_per_page)
            else:
                # If joins are not required
                res = model.query.options(selectinloads).filter(*filter_attrs).order_by(
                    *sort_attrs).paginate(page, limit, False, max_per_page)
            data = [r.as_dict(q_tz)
                    for r in res.items] if len(res.items) > 0 else []

            # Returning data and meta
            return jsonify({"data": data,
                            "meta": {"success": True,
                                     "count": res.total}})
        # If something goes wrong
        except Exception as e:
            return jsonify({"data": {},
                            "meta": {"success": False,
                                     "errors": str(e)}}), 500

# Set the route and accepted methods
@mod_role_api_route.route('', methods=['POST'])
@ensure_authorized
def create_role_api_route():
    # For POST method
    if request.method == 'POST':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = CreateRoleAPIRouteForm.from_json(request.json)
            # Getting the model
            model = RoleAPIRoute

            # Validating provided data
            if form.validate():
                # Checking if role exists
                if session.query(Role).get(form.role_id.data) is None:
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": _("No role found")}}), 404
                # Checking if route with selected method is already defined for the role
                if session.query(model).filter_by(
                        route=form.route.data,
                        method=form.method.data,
                        role_id=form.role_id.data,
                    ).first():
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": _("The route on the selected method is "
                                                        "already in use for this role.")}}), 400

                try:
                    # Creating new item
                    item = model(
                        route=form.route.data,
                        method=form.method.data,
                        role_id=form.role_id.data,
                        )
                    session.add(item)
                    session.flush()
                    session.commit()
                    return jsonify({"data": item.as_dict(),
                                    "meta": {"success": True}})
                # If an error occurrs
                except Exception as e:
                    session.rollback()
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": str(e)}}), 500
            
            # If something goes wrong
            else:
                # Returning the data to the request
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": form.errors}}), 400

# Set the route and accepted methods
@mod_role_api_route.route('/<int:id>', methods=['GET'])
@ensure_authorized
def get_role_api_route_by_id(id):
    # For GET method
    if request.method == 'GET':
        # Creating the session for database communication
        with AppSession() as session:
            # Defining the class for the data model, must be updated for different models
            model = RoleAPIRoute
            selectinloads = eval(''.join(f'selectinload({r}), ' for r in list(model.__mapper__.relationships)))

            # Searching item by ID
            role = session.query(model).options(selectinloads).get(id)

            # If item is found
            if role:
                return jsonify({"data": role.as_dict(),
                                "meta": {"success": True}})
            
            # If no item is found
            return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("No item found")}}), 404

# Set the route and accepted methods
@mod_role_api_route.route('/<int:id>', methods=['DELETE'])
@ensure_authorized
def delete_role_api_route(id):
    # For DELETE method
    if request.method == 'DELETE':
        # Creating the session for database communication
        with AppSession() as session:
            # Searching item by ID
            item = session.query(RoleAPIRoute).filter_by(id=id).first()

            # If the item is found
            if item:
                try:
                    session.delete(item)
                    session.commit()
                    return jsonify({"data": '',
                                    "meta": {"success": True}}), 204
                # If an error occurrs
                except Exception as e:
                    session.rollback()
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": str(e)}}), 500
            
            # If no item is found
            return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("No item found")}}), 404

# Set the route and accepted methods
@mod_role_web_action.route('', methods=['GET'])
@ensure_authorized
def index_role_web_action():
    # For GET method
    if request.method == 'GET':
        # Pagination
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=25, type=int)
        # Setting up a maximum number of results per page, even if limit exceeds it
        max_per_page = 250
        # Filtering and sorting
        filter = request.args.get('filter', default='[]', type=str)
        sort = request.args.get('sort', default='[]', type=str)
        # Query timezone
        timezone = request.args.get('timezone', default=os.getenv('TZ', 'UTC'), type=str)
        try: q_tz = pytz.timezone(timezone)
        except: q_tz = pytz.timezone(os.getenv('TZ', 'UTC'))

        # Defining the class for the data model, must be updated for different models
        model = RoleWebAction
        selectinloads = eval(''.join(f'selectinload({r}), ' for r in list(model.__mapper__.relationships)))

        # Trying to obtain data from models
        try:
            # Retrieving the sorting attributes
            sort_attrs = get_sort_attrs(model, sort)
            # Retrieving the join relationship models
            join_attrs = get_join_attrs(model, filter)
            # Retrieving the filtering attributes
            filter_attrs = get_filter_attrs(model, filter, q_tz)

            # Searching itens by filters and sorting
            if (len(join_attrs) > 0):
                # If joins are required
                res = model.query.options(selectinloads).join(*join_attrs).filter(
                    *filter_attrs).order_by(*sort_attrs).paginate(page, limit, False, max_per_page)
            else:
                # If joins are not required
                res = model.query.options(selectinloads).filter(*filter_attrs).order_by(
                    *sort_attrs).paginate(page, limit, False, max_per_page)
            data = [r.as_dict(q_tz)
                    for r in res.items] if len(res.items) > 0 else []

            # Returning data and meta
            return jsonify({"data": data,
                            "meta": {"success": True,
                                     "count": res.total}})
        # If something goes wrong
        except Exception as e:
            return jsonify({"data": {},
                            "meta": {"success": False,
                                     "errors": str(e)}}), 500

# Set the route and accepted methods
@mod_role_web_action.route('', methods=['POST'])
@ensure_authorized
def create_role_web_action():
    # For POST method
    if request.method == 'POST':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = CreateRoleWebActionForm.from_json(request.json)
            # Getting the model
            model = RoleWebAction

            # Validating provided data
            if form.validate():
                # Checking if role exists
                if session.query(Role).get(form.role_id.data) is None:
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": _("No role found")}}), 404
                # Checking if action is already defined for the role
                if session.query(model).filter_by(
                        action=form.action.data,
                        role_id=form.role_id.data,
                    ).first():
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": _("The action is already in use for this role.")}}), 400

                try:
                    # Creating new item
                    item = model(
                        action=form.action.data,
                        role_id=form.role_id.data,
                        )
                    session.add(item)
                    session.flush()
                    session.commit()
                    return jsonify({"data": item.as_dict(),
                                    "meta": {"success": True}})
                # If an error occurrs
                except Exception as e:
                    session.rollback()
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": str(e)}}), 500
            
            # If something goes wrong
            else:
                # Returning the data to the request
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": form.errors}}), 400

# Set the route and accepted methods
@mod_role_web_action.route('/<int:id>', methods=['GET'])
@ensure_authorized
def get_role_web_action_by_id(id):
    # For GET method
    if request.method == 'GET':
        # Creating the session for database communication
        with AppSession() as session:
            # Defining the class for the data model, must be updated for different models
            model = RoleWebAction
            selectinloads = eval(''.join(f'selectinload({r}), ' for r in list(model.__mapper__.relationships)))

            # Searching item by ID
            role = session.query(model).options(selectinloads).get(id)

            # If item is found
            if role:
                return jsonify({"data": role.as_dict(),
                                "meta": {"success": True}})

            # If no item is found
            return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("No item found")}}), 404

# Set the route and accepted methods
@mod_role_web_action.route('/<int:id>', methods=['DELETE'])
@ensure_authorized
def delete_role_web_action(id):
    # For DELETE method
    if request.method == 'DELETE':
        # Creating the session for database communication
        with AppSession() as session:
            # Searching item by ID
            item = session.query(RoleWebAction).filter_by(id=id).first()

            # If the item is found
            if item:
                try:
                    session.delete(item)
                    session.commit()
                    return jsonify({"data": '',
                                    "meta": {"success": True}}), 204
                # If an error occurrs
                except Exception as e:
                    session.rollback()
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": str(e)}}), 500
            
            # If no item is found
            return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("No item found")}}), 404

# Set the route and accepted methods
@mod_role_mobile_action.route('', methods=['GET'])
@ensure_authorized
def index_role_mobile_action():
    # For GET method
    if request.method == 'GET':
        # Pagination
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=25, type=int)
        # Setting up a maximum number of results per page, even if limit exceeds it
        max_per_page = 250
        # Filtering and sorting
        filter = request.args.get('filter', default='[]', type=str)
        sort = request.args.get('sort', default='[]', type=str)
        # Query timezone
        timezone = request.args.get('timezone', default=os.getenv('TZ', 'UTC'), type=str)
        try: q_tz = pytz.timezone(timezone)
        except: q_tz = pytz.timezone(os.getenv('TZ', 'UTC'))

        # Defining the class for the data model, must be updated for different models
        model = RoleMobileAction
        selectinloads = eval(''.join(f'selectinload({r}), ' for r in list(model.__mapper__.relationships)))

        # Trying to obtain data from models
        try:
            # Retrieving the sorting attributes
            sort_attrs = get_sort_attrs(model, sort)
            # Retrieving the join relationship models
            join_attrs = get_join_attrs(model, filter)
            # Retrieving the filtering attributes
            filter_attrs = get_filter_attrs(model, filter, q_tz)

            # Searching itens by filters and sorting
            if (len(join_attrs) > 0):
                # If joins are required
                res = model.query.options(selectinloads).join(*join_attrs).filter(
                    *filter_attrs).order_by(*sort_attrs).paginate(page, limit, False, max_per_page)
            else:
                # If joins are not required
                res = model.query.options(selectinloads).filter(*filter_attrs).order_by(
                    *sort_attrs).paginate(page, limit, False, max_per_page)
            data = [r.as_dict(q_tz)
                    for r in res.items] if len(res.items) > 0 else []

            # Returning data and meta
            return jsonify({"data": data,
                            "meta": {"success": True,
                                     "count": res.total}})
        # If something goes wrong
        except Exception as e:
            return jsonify({"data": {},
                            "meta": {"success": False,
                                     "errors": str(e)}}), 500

# Set the route and accepted methods
@mod_role_mobile_action.route('', methods=['POST'])
@ensure_authorized
def create_role_mobile_action():
    # For POST method
    if request.method == 'POST':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = CreateRoleMobileActionForm.from_json(request.json)
            # Getting the model
            model = RoleMobileAction

            # Validating provided data
            if form.validate():
                # Checking if role exists
                if session.query(Role).get(form.role_id.data) is None:
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": _("No role found")}}), 404
                # Checking if action is already defined for the role
                if session.query(model).filter_by(
                        action=form.action.data,
                        role_id=form.role_id.data,
                    ).first():
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": _("The action is already in use for this role.")}}), 400

                try:
                    # Creating new item
                    item = model(
                        action=form.action.data,
                        role_id=form.role_id.data,
                        )
                    session.add(item)
                    session.flush()
                    session.commit()
                    return jsonify({"data": item.as_dict(),
                                    "meta": {"success": True}})
                # If an error occurrs
                except Exception as e:
                    session.rollback()
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": str(e)}}), 500

            # If something goes wrong
            else:
                # Returning the data to the request
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": form.errors}}), 400

# Set the route and accepted methods
@mod_role_mobile_action.route('/<int:id>', methods=['GET'])
@ensure_authorized
def get_role_mobile_action_by_id(id):
    # For GET method
    if request.method == 'GET':
        # Creating the session for database communication
        with AppSession() as session:
            # Defining the class for the data model, must be updated for different models
            model = RoleMobileAction
            selectinloads = eval(''.join(f'selectinload({r}), ' for r in list(model.__mapper__.relationships)))

            # Searching item by ID
            role = session.query(model).options(selectinloads).get(id)

            # If item is found
            if role:
                return jsonify({"data": role.as_dict(),
                                "meta": {"success": True}})
            
            # If no item is found
            return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("No item found")}}), 404

# Set the route and accepted methods
@mod_role_mobile_action.route('/<int:id>', methods=['DELETE'])
@ensure_authorized
def delete_role_mobile_action(id):
    # For DELETE method
    if request.method == 'DELETE':
        # Creating the session for database communication
        with AppSession() as session:
            # Searching item by ID
            item = session.query(RoleMobileAction).filter_by(id=id).first()

            # If the item is found
            if item:
                try:
                    session.delete(item)
                    session.commit()
                    return jsonify({"data": '',
                                    "meta": {"success": True}}), 204
                # If an error occurrs
                except Exception as e:
                    session.rollback()
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": str(e)}}), 500
            
            # If no item is found
            return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("No item found")}}), 404
