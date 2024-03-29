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
from sqlalchemy import or_

# Session maker to allow database communication
from app import AppSession

# Import dependencies
import pytz

# Middlewares
from app.middleware import ensure_authenticated, ensure_authorized

# Import module forms
from app.modules.log.forms import *

# Import module models
from app.modules.log.models import *
from app.modules.document.models import *
from app.modules.users.models import *
from app.modules.settings.models import *

# Utilities functions
from app.modules.utils import get_sort_attrs, get_join_attrs, get_filter_attrs

# Define the blueprint: 'auth', set its url prefix: app.url/auth
mod_log = Blueprint("logs", __name__, url_prefix="/logs")


# Set the route and accepted methods
@mod_log.route("", methods=["GET"])
@ensure_authenticated
def index_log():
    # Only GET method is allowed, so we don't have to check the method here
    # Pagination
    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", default=25, type=int)
    # Setting up a maximum number of results per page, even if limit exceeds it
    max_per_page = 250
    # Filtering and sorting
    filter = request.args.get("filter", default="[]", type=str)
    sort = request.args.get("sort", default="[]", type=str)
    # Query timezone
    timezone = request.args.get("timezone", default=os.getenv("TZ", "UTC"), type=str)
    try:
        q_tz = pytz.timezone(timezone)
    except:
        q_tz = pytz.timezone(os.getenv("TZ", "UTC"))

    # Defining the class for the data model, must be updated for different models
    model = Log
    selectinloads = eval(
        "".join(f"selectinload({r}), " for r in list(model.__mapper__.relationships))
    )

    # Trying to obtain data from models
    try:
        # Retrieving the sorting attributes
        sort_attrs = get_sort_attrs(model, sort)
        # Retrieving the join relationship models
        join_attrs = get_join_attrs(model, filter, sort)
        # Retrieving the filtering attributes
        filter_attrs = get_filter_attrs(model, filter, q_tz)

        # Searching itens by filters and sorting
        if len(join_attrs) > 0:
            # If joins are required
            res = (
                model.query.options(selectinloads)
                .join(*join_attrs)
                .filter(*filter_attrs)
                .order_by(*sort_attrs)
                .paginate(page, limit, False, max_per_page)
            )
        else:
            # If joins are not required
            res = (
                model.query.options(selectinloads)
                .filter(*filter_attrs)
                .order_by(*sort_attrs)
                .paginate(page, limit, False, max_per_page)
            )
        data = [r.as_dict(q_tz) for r in res.items] if len(res.items) > 0 else []

        # Returning data and meta
        return jsonify({"data": data, "meta": {"success": True, "count": res.total}})
    # If something goes wrong
    except Exception as e:
        return jsonify({"data": {}, "meta": {"success": False, "errors": str(e)}}), 500


# Set the route and accepted methods
@mod_log.route("", methods=["POST"])
@ensure_authorized
def create_log():
    # Only POST method is allowed, so we don't have to check the method here
    # If data form is submitted
    form = CreateLogForm.from_json(request.json)
    # Getting the model
    model = Log

    # If something goes wrong when validating provided data
    if not form.validate():
        # Returning the data to the request
        return (
            jsonify({"data": [], "meta": {"success": False, "errors": form.errors}}),
            400,
        )

    # Creating a dict with the possible model names
    # TODO: must be updated if other models should be allowed
    model_names = {
        "User": User,
    }

    # Checking if model name is valid
    if form.model_name.data not in model_names.keys():
        return (
            jsonify(
                {
                    "data": [],
                    "meta": {"success": False, "errors": _("Model not applicable")},
                }
            ),
            400,
        )
    # Checking if model exists
    if model_names[form.model_name.data].query.get(form.model_id.data) is None:
        return (
            jsonify(
                {"data": [], "meta": {"success": False, "errors": _("No model found")}}
            ),
            400,
        )

    # Creating the session for database communication
    with AppSession() as session:
        try:
            # Creating new item
            item = model(
                ip_address=request.environ.get("HTTP_X_REAL_IP", request.remote_addr),
                user_id=g.user.id,
                **request.json,
            )
            session.add(item)
            session.flush()
            session.commit()
            return jsonify({"data": item.as_dict(), "meta": {"success": True}})
        # If an error occurrs
        except Exception as e:
            session.rollback()
            return (
                jsonify({"data": [], "meta": {"success": False, "errors": str(e)}}),
                500,
            )


# Set the route and accepted methods
@mod_log.route("/<int:id>", methods=["GET"])
@ensure_authenticated
def get_log_by_id(id):
    # Only GET method is allowed, so we don't have to check the method here

    # Creating a dict with the possible model names
    # TODO: must be updated if other models should be allowed
    model_names = {
        "User": User,
    }

    # Creating the session for database communication
    with AppSession() as session:
        # Getting the model
        model = Log
        selectinloads = eval(
            "".join(
                f"selectinload({r}), " for r in list(model.__mapper__.relationships)
            )
        )

        # Searching item by ID
        item = session.query(model).options(selectinloads).get(id)

        # If no item is found
        if item is None:
            return (
                jsonify(
                    {
                        "data": [],
                        "meta": {"success": False, "errors": _("No item found")},
                    }
                ),
                404,
            )

        # Otherwise, we get the item data as dict
        data = item.as_dict()

        # Appending the model data, if a valid model name is set
        if data["model_name"] in model_names.keys():
            data["model"] = (
                session.query(model_names[data["model_name"]])
                .get(data["model_id"])
                .as_dict()
            )

        # And return the resulting data
        return jsonify({"data": data, "meta": {"success": True}})


# Set the route and accepted methods
@mod_log.route("/<int:id>", methods=["DELETE"])
@ensure_authorized
def delete_log(id):
    # Only DELETE method is allowed, so we don't have to check the method here
    # Creating the session for database communication
    with AppSession() as session:
        # Searching item by ID
        item = session.query(Log).get(id)

        # If no item is found
        if not item:
            return (
                jsonify(
                    {
                        "data": [],
                        "meta": {"success": False, "errors": _("No item found")},
                    }
                ),
                404,
            )

        # If the item is found
        try:
            session.delete(item)
            session.commit()
            return jsonify({"data": "", "meta": {"success": True}}), 204
        # If an error occurrs
        except Exception as e:
            session.rollback()
            return (
                jsonify({"data": [], "meta": {"success": False, "errors": str(e)}}),
                500,
            )
