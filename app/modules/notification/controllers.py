# -*- coding: utf-8 -*-
"""
Refs:
    * Flask Request Documentation: https://tedboy.github.io/flask/generated/generated/flask.Request.html
    * SQLAlchemy Operator Reference: https://docs.sqlalchemy.org/en/14/core/operators.html
    
"""

# Import flask dependencies
from flask import Blueprint, request, jsonify, g
from flask_babel import _

# Function to be called on 'eval', in order to join models relationships
from sqlalchemy.orm import selectinload

# Session maker to allow database communication
from app import AppSession

# Config variables
from config import tz
# Import dependencies
from datetime import datetime
import pytz

# Middlewares
from app.middleware import ensure_authenticated, ensure_authorized

# Import module forms
from app.modules.notification.forms import *

# Import module models
from app.modules.notification.models import *
from app.modules.users.models import *
from app.modules.settings.models import *

# Utilities functions
from app.modules.utils import get_sort_attrs, get_join_attrs, \
    get_filter_attrs
from app.modules.notification.utils import *

# Define the blueprint: 'auth', set its url prefix: app.url/auth
mod_notification = Blueprint('notifications', __name__, url_prefix='/notifications')

# Set the route and accepted methods
@mod_notification.route('', methods=['GET'])
@ensure_authorized
def index_notification():
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
        model = Notification
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
                    *filter_attrs).\
                    order_by(*sort_attrs).paginate(page, limit, False, max_per_page)
            else:
                # If joins are not required
                res = model.query.options(selectinloads).filter(
                    *filter_attrs).\
                    order_by(
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
@mod_notification.route('/my', methods=['GET'])
@ensure_authenticated
def index_my_notification():
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
        model = Notification
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
                res = model.query.options(selectinloads).\
                    join(*join_attrs).filter(*filter_attrs).\
                    filter_by(user_id=g.user.id).\
                    order_by(*sort_attrs).paginate(page, limit, False, max_per_page)
            else:
                # If joins are not required
                res = model.query.options(selectinloads).\
                    filter(*filter_attrs).\
                    filter_by(user_id=g.user.id).\
                    order_by(
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
@mod_notification.route('', methods=['POST'])
@ensure_authorized
def create_notification():
    # For POST method
    if request.method == 'POST':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = CreateNotificationForm.from_json(request.json)
            # Getting the model
            model = Notification

            # Validating provided data
            if form.validate():
                try:
                    # Checking if user exists
                    user = session.query(User).get(form.user_id.data)
                    if user is None:
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": _("No user found")}}), 400

                    # Creating new item
                    item = model(
                        title=form.title.data,
                        description=form.description.data,
                        user_id=form.user_id.data,
                        web_action=form.web_action.data,
                        mobile_action=form.mobile_action.data,
                        )
                    session.add(item)
                    session.flush()
                    session.commit()

                    # Notifying user on front-end
                    notify_user_via_socketio(item.user_id, item.title, item.description, session)
                    # Notifying user on mobile application
                    notify_user_via_push_notification(item.user_id, item.title, item.description, session)

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
@mod_notification.route('/<int:id>', methods=['GET'])
@ensure_authenticated
def get_notification_by_id(id):
    # For GET method
    if request.method == 'GET':
        # Creating the session for database communication
        with AppSession() as session:
            # Getting the model
            model = Notification
            selectinloads = eval(''.join(f'selectinload({r}), ' for r in list(model.__mapper__.relationships)))
            
            # Searching item by ID
            item = session.query(model).options(selectinloads).get(id)

            # If no item is found
            if item is None:
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("No item found")}}), 400

            # Otherwise
            data = item.as_dict()

            # If item is found
            if data:
                return jsonify({"data": data,
                                "meta": {"success": True}})

# Set the route and accepted methods
@mod_notification.route('/<int:id>', methods=['PUT'])
@ensure_authorized
def update_notification(id):
    # For PUT method
    if request.method == 'PUT':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = UpdateNotificationForm.from_json(request.json)
            # Getting the model
            model = Notification

            # Validating provided data
            if form.validate():
                try:
                    # Updating the item
                    item = session.query(model).get(id)
                    if item:
                        # Updating object attributes
                        for key in request.json.keys():
                            # Allows update only for fields set in form
                            if (key in list(form._fields.keys())):
                                setattr(item, key, getattr(form, key).data)

                        try:
                            session.commit()
                            return jsonify({"data": item.as_dict(),
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
                                            "errors": _("No item found")}}), 400

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
@mod_notification.route('/<int:id>/read', methods=['PATCH'])
@ensure_authenticated
def set_read_notification(id):
    # For PATCH method
    if request.method == 'PATCH':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = ReadNotificationForm.from_json(request.json)
            # Getting the model
            model = Notification

            # Validating provided data
            if form.validate():
                try:
                    # Updating the item
                    item = session.query(model).get(id)
                    if item:
                        # Checking if current user is the notified user
                        if item.user_id != g.user.id:
                            return jsonify({"data": [],
                                            "meta": {"success": False,
                                                    "errors": _("Only the notified user can set this notification as read")}}), 400
                        # Checking if read date was provided
                        if form.read_at.data is None: item.read_at = datetime.now(tz)
                        # The read date cannot be in the future
                        else:
                            if form.read_at.data > datetime.now(tz):
                                return jsonify({"data": [],
                                                "meta": {"success": False,
                                                        "errors": _("The read date cannot be in the future.")}}), 400
                            item.read_at = form.read_at.data
                        # Setting the item read flag
                        item.is_read = form.is_read.data
                        # If notification is set as unread, we'll clear the read date
                        if int(form.is_read.data) == 0: item.read_at = None
                        
                        try:
                            session.commit()
                            return jsonify({"data": item.as_dict(),
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
                                            "errors": _("No item found")}}), 400

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
@mod_notification.route('/<int:id>', methods=['DELETE'])
@ensure_authorized
def delete_notification(id):
    # For DELETE method
    if request.method == 'DELETE':
        # Creating the session for database communication
        with AppSession() as session:
            # Searching item by ID
            item = session.query(Notification).filter_by(id=id).first()

            # If the item is found
            if item:
                # Checking if there are any other associated items to the item
                # TODO: check for associated items
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
                                        "errors": _("No item found")}}), 400

# Set the route and accepted methods
@mod_notification.route('/<int:id>/my', methods=['DELETE'])
@ensure_authenticated
def delete_my_notification(id):
    # For DELETE method
    if request.method == 'DELETE':
        # Creating the session for database communication
        with AppSession() as session:
            # Searching item by ID
            item = session.query(Notification).filter_by(id=id).first()

            # If the item is found
            if item:
                # Checking if the user is the notified user, if not, throw an error
                if item.user_id != g.user.id:
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": _("Only the notified user can delete this notification")}}), 400
                # Checking if there are any other associated items to the item
                # TODO: check for associated items
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
                                        "errors": _("No item found")}}), 400
