"""Controllers and blueprins/endpoints for the notifications module."""

from datetime import datetime
import pytz

from flask import Blueprint, request, jsonify, g
from flask_babel import _
from flasgger import swag_from
from sqlalchemy.orm import selectinload  # This function is called within 'eval'

from app import AppSession
from config import tz
from app.middleware import ensure_authenticated, ensure_authorized
from app.modules.notification.forms import *
from app.modules.notification.models import *
from app.modules.users.models import *
from app.modules.commons.models import *
from app.modules.utils import get_sort_attrs, get_join_attrs, get_filter_attrs
from app.modules.notification.utils import *

# Blueprints for the model
mod_notification = Blueprint("notifications", __name__, url_prefix="/notifications")


@mod_notification.route("", methods=["GET"])
@ensure_authorized
@swag_from("swagger/index_item.yml")
def index_notification():
    """Lists the existing notifications."""

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

    model = Notification
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


@mod_notification.route("/my", methods=["GET"])
@ensure_authenticated
@swag_from("swagger/index_my_item.yml")
def index_my_notification():
    """Lists the notifications for a specific user."""

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

    model = Notification
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
                .filter_by(user_id=g.user.id)
                .order_by(*sort_attrs)
                .paginate(page, limit, False, max_per_page)
            )
        else:
            # If joins are not required
            res = (
                model.query.options(selectinloads)
                .filter(*filter_attrs)
                .filter_by(user_id=g.user.id)
                .order_by(*sort_attrs)
                .paginate(page, limit, False, max_per_page)
            )
        data = [r.as_dict(q_tz) for r in res.items] if len(res.items) > 0 else []

        return jsonify({"data": data, "meta": {"success": True, "count": res.total}})

    except Exception as e:
        return jsonify({"data": {}, "meta": {"success": False, "errors": str(e)}}), 500


@mod_notification.route("", methods=["POST"])
@ensure_authorized
@swag_from("swagger/create_item.yml")
def create_notification():
    """Creates a new notification for an user."""

    # Validates provided data
    form = CreateNotificationForm.from_json(request.json)
    if not form.validate():
        return (
            jsonify({"data": [], "meta": {"success": False, "errors": form.errors}}),
            400,
        )

    with AppSession() as session:
        model = Notification
        # Checking if user exists
        user = session.query(User).get(form.user_id.data)
        if user is None:
            return (
                jsonify(
                    {
                        "data": [],
                        "meta": {"success": False, "errors": _("No user found")},
                    }
                ),
                400,
            )

        try:
            # Creating new item
            item = model(**request.json)
            session.add(item)
            session.flush()
            session.commit()

            # Notifying user on front-end
            notify_user_via_socketio(
                item.user_id, item.title, item.description, session
            )
            # Notifying user on mobile application
            notify_user_via_push_notification(
                item.user_id, item.title, item.description, session
            )

            return jsonify({"data": item.as_dict(), "meta": {"success": True}})

        except Exception as e:
            session.rollback()
            return (
                jsonify({"data": [], "meta": {"success": False, "errors": str(e)}}),
                500,
            )


@mod_notification.route("/<int:id>", methods=["GET"])
@ensure_authenticated
@swag_from("swagger/get_item_by_id.yml")
def get_notification_by_id(id):
    """Gets an existing notification by its id."""

    with AppSession() as session:
        model = Notification
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


@mod_notification.route("/<int:id>", methods=["PUT"])
@ensure_authorized
def update_notification(id):
    """
    Updates an existing notification.

    Note: this endpoint might not be really useful for most of web apps. It's not likely that a notification would be
    updated. We can think about removing this later.
    """

    # Validates provided data
    form = UpdateNotificationForm.from_json(request.json)
    if not form.validate():
        return (
            jsonify({"data": [], "meta": {"success": False, "errors": form.errors}}),
            400,
        )

    with AppSession() as session:
        model = Notification
        # Getting the item to be updated
        item = session.query(model).get(id)
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

        # Updating object attributes
        if form.title.data is not None:
            item.title = form.title.data
        if form.description.data is not None:
            item.description = form.description.data
        if form.web_action.data is not None:
            item.web_action = form.web_action.data
        if form.mobile_action.data is not None:
            item.mobile_action = form.mobile_action.data
        try:
            session.commit()
            return jsonify({"data": item.as_dict(), "meta": {"success": True}})

        except Exception as e:
            session.rollback()
            return (
                jsonify({"data": [], "meta": {"success": False, "errors": str(e)}}),
                500,
            )


@mod_notification.route("/<int:id>/read", methods=["PUT"])
@ensure_authenticated
@swag_from("swagger/set_read_notification.yml")
def set_read_notification(id):
    """Sets a notification as read/unread."""

    # Validates provided data
    form = ReadNotificationForm.from_json(request.json)
    if not form.validate():
        return (
            jsonify({"data": [], "meta": {"success": False, "errors": form.errors}}),
            400,
        )

    # Setting default read date if not provided
    if not form.read_at.data:
        form.read_at.data = datetime.now(tz)
    # The read date cannot be in the future
    if form.read_at.data > datetime.now(tz):
        return (
            jsonify(
                {
                    "data": [],
                    "meta": {
                        "success": False,
                        "errors": _("The read date cannot be in the future."),
                    },
                }
            ),
            400,
        )

    with AppSession() as session:
        model = Notification
        # Getting the item to be updated
        item = session.query(model).get(id)
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

        # Checking if current user is the notified user
        if item.user_id != g.user.id:
            return (
                jsonify(
                    {
                        "data": [],
                        "meta": {
                            "success": False,
                            "errors": _(
                                "Only the notified user can set this notification as read"
                            ),
                        },
                    }
                ),
                400,
            )

        # Update the item
        item.read_at = form.read_at.data
        item.is_read = form.is_read.data
        # If notification is set as unread, we'll clear the read date
        if int(form.is_read.data) == 0:
            item.read_at = None

        try:
            session.commit()
            return jsonify({"data": item.as_dict(), "meta": {"success": True}})

        except Exception as e:
            session.rollback()
            return (
                jsonify({"data": [], "meta": {"success": False, "errors": str(e)}}),
                500,
            )


@mod_notification.route("/read-all", methods=["PUT"])
@ensure_authenticated
@swag_from("swagger/read_all_notifications.yml")
def read_all_notifications():
    """Reads all notifications for the requestor user."""

    with AppSession() as session:
        model = Notification
        # Getting the items to be updated (all unread notifications for the user)
        items = (
            session.query(model)
            .filter(model.user_id == g.user.id, model.is_read == 0)
            .all()
        )
        # Setting all notifications as read
        for item in items:
            item.is_read = 1
            item.read_at = datetime.now(tz)

        try:
            session.commit()
            return jsonify(
                {
                    "data": {"read_notifcations_count": len(items)},
                    "meta": {"success": True},
                }
            )

        except Exception as e:
            session.rollback()
            return (
                jsonify({"data": [], "meta": {"success": False, "errors": str(e)}}),
                500,
            )


@mod_notification.route("/<int:id>", methods=["DELETE"])
@ensure_authorized
@swag_from("swagger/delete_item.yml")
def delete_notification(id):
    """Deletes an existing notification."""

    with AppSession() as session:
        # Searching item by ID
        item = session.query(Notification).get(id)

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


@mod_notification.route("/<int:id>/my", methods=["DELETE"])
@ensure_authenticated
@swag_from("swagger/delete_my_item.yml")
def delete_my_notification(id):
    """Deletes an existing notification from the requestor user."""

    with AppSession() as session:
        # Searching item by ID
        item = session.query(Notification).get(id)

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

        # Checking if the requesting user is the notified user
        if item.user_id != g.user.id:
            return (
                jsonify(
                    {
                        "data": [],
                        "meta": {
                            "success": False,
                            "errors": _(
                                "Only the notified user can delete this notification"
                            ),
                        },
                    }
                ),
                403,
            )

        # Deleting the item
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
