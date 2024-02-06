# -*- coding: utf-8 -*-

# Functools module
from functools import wraps

# Required modules
from flask import request, g, jsonify
from flask_babel import _

# SQLAlchemy auxiliary query options
from sqlalchemy import or_

# Import module models
from app.modules.users.models import *


# Middleware to get user data and check if it is authenticated
def ensure_authenticated(func):
    @wraps(func)
    def auth_function(*args, **kwargs):
        # If an auth header was provided
        try:
            # Getting user ID by token
            token = request.headers["Authorization"].split("Bearer ")[1]
            res = User.decode_auth_token(token)
            # If token is not valid
            if type(res) is not int:
                return (
                    jsonify(
                        {
                            "data": {},
                            "meta": {
                                "success": False,
                                "errors": _(
                                    "Authentication failed. Please login to access the resource."
                                ),
                            },
                        }
                    ),
                    401,
                )
            # Searching user by ID
            user = User.query.get(res)
            # If no user is found
            if user is None:
                return (
                    jsonify(
                        {
                            "data": {},
                            "meta": {
                                "success": False,
                                "errors": _(
                                    "Authentication failed. Please login to access the resource."
                                ),
                            },
                        }
                    ),
                    401,
                )
            # If user is found
            g.user = user
            g.role = user.role if user.role else None

        # Otherwise
        except Exception as e:
            return (
                jsonify(
                    {
                        "data": {},
                        "meta": {
                            "success": False,
                            "errors": (
                                _(
                                    "Authentication failed. Please login to access the resource."
                                ),
                                str(e),
                            ),
                        },
                    }
                ),
                401,
            )
        # Continue the execution
        return func(*args, **kwargs)

    return auth_function


# Middleware to get user data and check if it is authorized
def ensure_authorized(func):
    @wraps(func)
    # First we check if user is authorized
    @ensure_authenticated
    def auth_function(*args, **kwargs):
        try:
            authorized_flag = False
            # Looking for path parameters and replacing in the requested route
            route_path = request.path
            path_params = request.view_args
            if bool(path_params):
                for p in path_params:
                    route_path = route_path.replace(str(path_params[p]), ":" + str(p))

            # Now we must ensure the user has access rights for the method on the resource
            authorizations = RoleAPIRoute.query.filter(
                or_(RoleAPIRoute.route == route_path, RoleAPIRoute.route == "*"),
                RoleAPIRoute.method == request.method,
                RoleAPIRoute.role_id == g.user.role_id,
            ).all()
            # If user role has access to all routes or to the specified one in the request
            if len(authorizations) >= 1:
                authorized_flag = True
            # Otherwise we return an error
            else:
                return (
                    jsonify(
                        {
                            "data": {},
                            "meta": {
                                "success": False,
                                "errors": _(
                                    "Authorization failed. Please use an account with the correct access rights."
                                ),
                            },
                        }
                    ),
                    403,
                )

        # Otherwise
        except Exception as e:
            return (
                jsonify(
                    {
                        "data": {},
                        "meta": {
                            "success": False,
                            "errors": (
                                _(
                                    "Authorization failed. Please use an account with the correct access rights."
                                ),
                                str(e),
                            ),
                        },
                    }
                ),
                403,
            )

        # If user is authorized, continue the execution
        if authorized_flag:
            return func(*args, **kwargs)

    return auth_function
