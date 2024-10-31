"""Controllers and blueprins/endpoints for the logs module."""

import pytz

from flask import Blueprint, request, jsonify, g
from flask_babel import _
from sqlalchemy.orm import selectinload  # This function is called within 'eval'

from app import AppSession
from app.middleware import ensure_authenticated, ensure_authorized
from app.modules.log.forms import *
from app.modules.log.models import *
from app.modules.document.models import *
from app.modules.users.models import *
from app.modules.settings.models import *
from app.modules.utils import get_sort_attrs, get_join_attrs, get_filter_attrs

# Blueprints for the model
mod_log = Blueprint("logs", __name__, url_prefix="/logs")


@mod_log.route("", methods=["GET"])
@ensure_authenticated
def index_log():
    """Lists the exsiting logs."""

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

    model = Log
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


@mod_log.route("", methods=["POST"])
@ensure_authorized
def create_log():
    """Creates a new log."""

    # Validates provided data
    form = CreateLogForm.from_json(request.json)
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

    with AppSession() as session:
        model = Log
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
        except Exception as e:
            session.rollback()
            return (
                jsonify({"data": [], "meta": {"success": False, "errors": str(e)}}),
                500,
            )


@mod_log.route("/<int:id>", methods=["GET"])
@ensure_authenticated
def get_log_by_id(id):
    """Gets an existing log by its id."""

    # Creating a dict with the possible model names
    # TODO: must be updated if other models should be allowed
    model_names = {
        "User": User,
    }

    with AppSession() as session:
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

        data = item.as_dict()

        # Appending the model data, if a valid model name is set
        if data["model_name"] in model_names.keys():
            data["model"] = (
                session.query(model_names[data["model_name"]])
                .get(data["model_id"])
                .as_dict()
            )

        return jsonify({"data": data, "meta": {"success": True}})


@mod_log.route("/<int:id>", methods=["DELETE"])
@ensure_authorized
def delete_log(id):
    """Deletes an existing log."""

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
