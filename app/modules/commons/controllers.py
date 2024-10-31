# -*- coding: utf-8 -*-
"""
Refs:
    * Flask Request Documentation: https://tedboy.github.io/flask/generated/generated/flask.Request.html
    * SQLAlchemy Operator Reference: https://docs.sqlalchemy.org/en/14/core/operators.html

"""

# Import flask dependencies
from flask import Blueprint, request, jsonify, g
from flask_babel import _
import os

# Swagger documentation
from flasgger import swag_from

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
from app.modules.commons.forms import *

# Import module models
from app.modules.commons.models import *

# Utilities functions
from app.modules.utils import get_sort_attrs, get_join_attrs, get_filter_attrs

# Define the blueprint: 'auth', set its url prefix: app.url/auth
mod_uf = Blueprint("ufs", __name__, url_prefix="/ufs")
mod_city = Blueprint("cities", __name__, url_prefix="/cities")


# Set the route and accepted methods
@mod_uf.route("", methods=["GET"])
@ensure_authorized
@swag_from("swagger/uf/index_item.yml")
def index_uf():
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
    model = UF

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
                model.query.join(*join_attrs)
                .filter(*filter_attrs)
                .order_by(*sort_attrs)
                .paginate(page, limit, False, max_per_page)
            )
        else:
            # If joins are not required
            res = (
                model.query.filter(*filter_attrs)
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
@mod_uf.route("", methods=["POST"])
@ensure_authorized
@swag_from("swagger/uf/create_item.yml")
def create_uf():
    # If data form is submitted
    form = CreateUFForm.from_json(request.json)

    # If something goes wrong when validating provided data
    if not form.validate():
        # Returning the data to the request
        return (
            jsonify({"data": [], "meta": {"success": False, "errors": form.errors}}),
            400,
        )

    # Creating the session for database communication
    with AppSession() as session:
        # Checking if field is already in use
        if session.query(UF).filter_by(code=form.code.data).first():
            return (
                jsonify(
                    {
                        "data": [],
                        "meta": {
                            "success": False,
                            "errors": _("This code is already in use."),
                        },
                    }
                ),
                400,
            )
        try:
            # Creating new item
            item = UF(**request.json)
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
@mod_uf.route("/<int:id>", methods=["GET"])
@ensure_authorized
@swag_from("swagger/uf/get_item_by_id.yml")
def get_uf_by_id(id):
    # Creating the session for database communication
    with AppSession() as session:
        # Searching item by ID
        item = session.query(UF).get(id)

        # If item is found
        if item:
            return jsonify({"data": item.as_dict(), "meta": {"success": True}})

        # If no item is found
        return (
            jsonify(
                {"data": [], "meta": {"success": False, "errors": _("No item found")}}
            ),
            404,
        )


# Set the route and accepted methods
@mod_uf.route("/<int:id>", methods=["PUT"])
@ensure_authorized
@swag_from("swagger/uf/update_item.yml")
def update_uf(id):
    # If data form is submitted
    form = UpdateUFForm.from_json(request.json)

    # If something goes wrong when validating provided data
    if not form.validate():
        # Returning the data to the request
        return (
            jsonify({"data": [], "meta": {"success": False, "errors": form.errors}}),
            400,
        )

    # Creating the session for database communication
    with AppSession() as session:
        # Getting the item to be updated
        item = session.query(UF).get(id)
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

        # Updating the item
        if form.code.data is not None:
            if form.code.data != item.code:
                # Checking if field is not already in use
                if session.query(UF).filter_by(code=form.code.data).first():
                    return (
                        jsonify(
                            {
                                "data": [],
                                "meta": {
                                    "success": False,
                                    "errors": _("This code is already in use."),
                                },
                            }
                        ),
                        400,
                    )
                else:
                    item.code = form.code.data
        if form.name.data is not None:
            item.name = form.name.data

        try:
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
@mod_uf.route("/<int:id>", methods=["DELETE"])
@ensure_authorized
@swag_from("swagger/uf/delete_item.yml")
def delete_uf(id):
    # Creating the session for database communication
    with AppSession() as session:
        # Searching item by ID
        item = session.query(UF).get(id)

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
        # Checking if there are relationships defined for the item
        # TODO: check for newly created relationships
        if City.query.filter(City.uf_id == id).first() is not None:
            return (
                jsonify(
                    {
                        "data": [],
                        "meta": {
                            "success": False,
                            "errors": _(
                                "There are other items associated with this item"
                            ),
                        },
                    }
                ),
                400,
            )
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


# Set the route and accepted methods
@mod_city.route("", methods=["GET"])
@ensure_authorized
@swag_from("swagger/city/index_item.yml")
def index_city():
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
    model = City
    # Getting the model relationships and evaluating the call string in order to load the relationships
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
@mod_city.route("", methods=["POST"])
@ensure_authorized
@swag_from("swagger/city/create_item.yml")
def create_city():
    # If data form is submitted
    form = CreateCityForm.from_json(request.json)

    # If something goes wrong when validating provided data
    if not form.validate():
        # Returning the data to the request
        return (
            jsonify({"data": [], "meta": {"success": False, "errors": form.errors}}),
            400,
        )

    # Creating the session for database communication
    with AppSession() as session:
        # Checking if UF exists
        if session.query(UF).get(form.uf_id.data) is None:
            return (
                jsonify(
                    {
                        "data": [],
                        "meta": {"success": False, "errors": _("No UF found")},
                    }
                ),
                404,
            )
        try:
            # Creating new item
            item = City(**request.json)
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
@mod_city.route("/<int:id>", methods=["GET"])
@ensure_authorized
@swag_from("swagger/city/get_item_by_id.yml")
def get_city_by_id(id):
    # Creating the session for database communication
    with AppSession() as session:
        # Getting the model
        model = City
        selectinloads = eval(
            "".join(
                f"selectinload({r}), " for r in list(model.__mapper__.relationships)
            )
        )

        # Searching item by ID
        item = session.query(model).options(selectinloads).get(id)

        # If item is found
        if item:
            return jsonify({"data": item.as_dict(), "meta": {"success": True}})

        # If no item is found
        return (
            jsonify(
                {"data": [], "meta": {"success": False, "errors": _("No item found")}}
            ),
            404,
        )


# Set the route and accepted methods
@mod_city.route("/<int:id>", methods=["PUT"])
@ensure_authorized
@swag_from("swagger/city/update_item.yml")
def update_city(id):
    # If data form is submitted
    form = UpdateCityForm.from_json(request.json)

    # If something goes wrong when validating provided data
    if not form.validate():
        # Returning the data to the request
        return (
            jsonify({"data": [], "meta": {"success": False, "errors": form.errors}}),
            400,
        )

    # Creating the session for database communication
    with AppSession() as session:
        # Getting the item to be updated
        item = session.query(City).get(id)
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

        # Updating the item
        # If a new UF was provided
        if form.uf_id.data:
            # Checking if UF exists
            uf = session.query(UF).get(form.uf_id.data)
            if uf is None:
                return (
                    jsonify(
                        {
                            "data": [],
                            "meta": {"success": False, "errors": _("No UF found")},
                        }
                    ),
                    400,
                )
            else:
                item.uf_id = form.uf_id.data
        if form.name.data is not None:
            item.name = form.name.data

        try:
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
@mod_city.route("/<int:id>", methods=["DELETE"])
@ensure_authorized
@swag_from("swagger/city/delete_item.yml")
def delete_city(id):
    # Creating the session for database communication
    with AppSession() as session:
        # Searching item by ID
        item = session.query(City).get(id)

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
        # Checking if there are relationships defined for the item
        # TODO: check for newly created relationships
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
