"""Controllers and blueprins/endpoints for the commons module."""

import os
import pytz

from flask import Blueprint, request, jsonify
from flask_babel import _
from sqlalchemy.orm import selectinload  # This function is called within 'eval'
from flasgger import swag_from

from app import AppSession
from app.middleware import ensure_authorized
from app.modules.commons.forms import *
from app.modules.commons.models import *
from app.modules.utils import get_sort_attrs, get_join_attrs, get_filter_attrs

# Blueprints for the models
mod_uf = Blueprint("ufs", __name__, url_prefix="/ufs")
mod_city = Blueprint("cities", __name__, url_prefix="/cities")


@mod_uf.route("", methods=["GET"])
@ensure_authorized
@swag_from("swagger/uf/index_item.yml")
def index_uf():
    """Lists the existing UFs."""

    # Pagination
    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", default=25, type=int)
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

    model = UF

    # Trying to obtain data from models
    try:
        sort_attrs = get_sort_attrs(model, sort)
        join_attrs = get_join_attrs(model, filter, sort)
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

        return jsonify({"data": data, "meta": {"success": True, "count": res.total}})

    except Exception as e:
        return jsonify({"data": {}, "meta": {"success": False, "errors": str(e)}}), 500


@mod_uf.route("", methods=["POST"])
@ensure_authorized
@swag_from("swagger/uf/create_item.yml")
def create_uf():
    """Creates a new UF."""

    # Validates provided data
    form = CreateUFForm.from_json(request.json)
    if not form.validate():
        return (
            jsonify({"data": [], "meta": {"success": False, "errors": form.errors}}),
            400,
        )

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
        except Exception as e:
            session.rollback()
            return (
                jsonify({"data": [], "meta": {"success": False, "errors": str(e)}}),
                500,
            )


@mod_uf.route("/<int:id>", methods=["GET"])
@ensure_authorized
@swag_from("swagger/uf/get_item_by_id.yml")
def get_uf_by_id(id):
    """Gets an existing UF by its id."""

    with AppSession() as session:
        # Searching item by ID
        item = session.query(UF).get(id)

        # If item is found
        if item:
            return jsonify({"data": item.as_dict(), "meta": {"success": True}})

        return (
            jsonify(
                {"data": [], "meta": {"success": False, "errors": _("No item found")}}
            ),
            404,
        )


@mod_uf.route("/<int:id>", methods=["PUT"])
@ensure_authorized
@swag_from("swagger/uf/update_item.yml")
def update_uf(id):
    """Updates an existing UF."""

    # Validates provided data
    form = UpdateUFForm.from_json(request.json)
    if not form.validate():
        return (
            jsonify({"data": [], "meta": {"success": False, "errors": form.errors}}),
            400,
        )

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

        except Exception as e:
            session.rollback()
            return (
                jsonify({"data": [], "meta": {"success": False, "errors": str(e)}}),
                500,
            )


@mod_uf.route("/<int:id>", methods=["DELETE"])
@ensure_authorized
@swag_from("swagger/uf/delete_item.yml")
def delete_uf(id):
    """Deletes an existing UF."""

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
        except Exception as e:
            session.rollback()
            return (
                jsonify({"data": [], "meta": {"success": False, "errors": str(e)}}),
                500,
            )


@mod_city.route("", methods=["GET"])
@ensure_authorized
@swag_from("swagger/city/index_item.yml")
def index_city():
    """Lists the existing cities."""

    # Pagination
    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", default=25, type=int)
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

    model = City
    selectinloads = eval(
        "".join(f"selectinload({r}), " for r in list(model.__mapper__.relationships))
    )

    # Trying to obtain data from models
    try:
        sort_attrs = get_sort_attrs(model, sort)
        join_attrs = get_join_attrs(model, filter, sort)
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

        return jsonify({"data": data, "meta": {"success": True, "count": res.total}})

    except Exception as e:
        return jsonify({"data": {}, "meta": {"success": False, "errors": str(e)}}), 500


@mod_city.route("", methods=["POST"])
@ensure_authorized
@swag_from("swagger/city/create_item.yml")
def create_city():
    """Creates a new city."""

    # Validates provided data
    form = CreateCityForm.from_json(request.json)
    if not form.validate():
        return (
            jsonify({"data": [], "meta": {"success": False, "errors": form.errors}}),
            400,
        )

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
        except Exception as e:
            session.rollback()
            return (
                jsonify({"data": [], "meta": {"success": False, "errors": str(e)}}),
                500,
            )


@mod_city.route("/<int:id>", methods=["GET"])
@ensure_authorized
@swag_from("swagger/city/get_item_by_id.yml")
def get_city_by_id(id):
    """Gets an existing city by its id."""

    with AppSession() as session:
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

        return (
            jsonify(
                {"data": [], "meta": {"success": False, "errors": _("No item found")}}
            ),
            404,
        )


@mod_city.route("/<int:id>", methods=["PUT"])
@ensure_authorized
@swag_from("swagger/city/update_item.yml")
def update_city(id):
    """Updates an existing city."""

    # Validates provided data
    form = UpdateCityForm.from_json(request.json)
    if not form.validate():
        return (
            jsonify({"data": [], "meta": {"success": False, "errors": form.errors}}),
            400,
        )

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

        except Exception as e:
            session.rollback()
            return (
                jsonify({"data": [], "meta": {"success": False, "errors": str(e)}}),
                500,
            )


@mod_city.route("/<int:id>", methods=["DELETE"])
@ensure_authorized
@swag_from("swagger/city/delete_item.yml")
def delete_city(id):
    """Deletes an existing city."""

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

        # Checking if there are relationships defined for the item
        # TODO: check for newly created relationships
        try:
            session.delete(item)
            session.commit()
            return jsonify({"data": "", "meta": {"success": True}}), 204
        except Exception as e:
            session.rollback()
            return (
                jsonify({"data": [], "meta": {"success": False, "errors": str(e)}}),
                500,
            )
