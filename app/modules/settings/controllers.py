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
from app.modules.settings.forms import *

# Import module models
from app.modules.settings.models import *
from app.modules.books.models import *

# Utilities functions
from app.modules.utils import get_sort_attrs, get_join_attrs, \
    get_filter_attrs

# Define the blueprint: 'auth', set its url prefix: app.url/auth
mod_library = Blueprint('libraries', __name__, url_prefix='/libraries')
mod_city = Blueprint('cities', __name__, url_prefix='/cities')
mod_country = Blueprint('countries', __name__, url_prefix='/countries')

# Set the route and accepted methods
@mod_library.route('', methods=['GET'])
@ensure_authorized
def index_library():
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
        model = Library
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
@mod_library.route('', methods=['POST'])
@ensure_authorized
def create_library():
    # For POST method
    if request.method == 'POST':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = CreateLibraryForm.from_json(request.json)

            # Validating provided data
            if form.validate():
                # Checking if field is already in use
                if session.query(Library).filter_by(name=form.name.data).first():
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": _("This name is already in use.")}}), 400
                try:
                    # Checking if city exists
                    if form.city_id.data and session.query(City).get(form.city_id.data) is None:
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": _("No city found")}}), 400
                    # Creating new item
                    item = Library(
                        name=form.name.data,
                        cnpj=form.cnpj.data if form.cnpj.data is not None else None,
                        cpf=form.cpf.data if form.cpf.data is not None else None,
                        city_id=form.city_id.data if form.city_id.data is not None else None,
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
@mod_library.route('/<int:id>', methods=['GET'])
@ensure_authorized
def get_library_by_id(id):
    # For GET method
    if request.method == 'GET':
        # Creating the session for database communication
        with AppSession() as session:
            # Getting the model
            model = Library
            selectinloads = eval(''.join(f'selectinload({r}), ' for r in list(model.__mapper__.relationships)))

            # Searching item by ID
            item = session.query(model).options(selectinloads).get(id)

            # If item is found
            if item:
                return jsonify({"data": item.as_dict(),
                                "meta": {"success": True}})
            
            # If no item is found
            return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("No item found")}}), 400

# Set the route and accepted methods
@mod_library.route('/<int:id>', methods=['PUT'])
@ensure_authorized
def update_library(id):
    # For PUT method
    if request.method == 'PUT':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = UpdateLibraryForm.from_json(request.json)

            # Validating provided data
            if form.validate():
                try:
                    # Updating the item
                    item = session.query(Library).get(id)
                    if item:
                        if form.name.data is not None:
                            if form.name.data != item.name:
                                # Checking if field is not already in use
                                if session.query(Library).filter_by(name=form.name.data).first():
                                    return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": _("This name is already in use.")}}), 400
                                else:
                                    item.name=form.name.data
                        if form.cnpj.data is not None:
                            item.cnpj=form.cnpj.data
                        if form.cpf.data is not None:
                            item.cpf=form.cpf.data
                        if form.city_id.data is not None:
                            # Checking if city exists
                            if form.city_id.data and session.query(City).get(form.city_id.data) is None:
                                return jsonify({"data": [],
                                                "meta": {"success": False,
                                                        "errors": _("No city found")}}), 400
                            item.city_id=form.city_id.data
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
@mod_library.route('/<int:id>', methods=['DELETE'])
@ensure_authorized
def delete_library(id):
    # For DELETE method
    if request.method == 'DELETE':
        # Creating the session for database communication
        with AppSession() as session:
            # Searching item by ID
            item = session.query(Library).filter_by(id=id).first()

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
                                        "errors": _("No item found")}}), 400

# Set the route and accepted methods
@mod_city.route('', methods=['GET'])
@ensure_authenticated
def index_city():
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
        model = City
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
@mod_city.route('', methods=['POST'])
@ensure_authorized
def create_city():
    # For POST method
    if request.method == 'POST':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = CreateCityForm.from_json(request.json)

            # Validating provided data
            if form.validate():
                try:
                    # Checking if country exists
                    if form.country_id.data and session.query(Country).get(form.country_id.data) is None:
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": _("No country found")}}), 400
                    # Creating new item
                    item = City(
                        name=form.name.data,
                        uf=form.uf.data,
                        country_id=form.country_id.data if form.country_id.data is not None else None,
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
@mod_city.route('/<int:id>', methods=['GET'])
@ensure_authenticated
def get_city_by_id(id):
    # For GET method
    if request.method == 'GET':
        # Creating the session for database communication
        with AppSession() as session:
            # Getting the model
            model = City
            selectinloads = eval(''.join(f'selectinload({r}), ' for r in list(model.__mapper__.relationships)))

            # Searching item by ID
            item = session.query(model).options(selectinloads).get(id)

            # If item is found
            if item:
                return jsonify({"data": item.as_dict(),
                                "meta": {"success": True}})
            
            # If no item is found
            return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("No item found")}}), 400

# Set the route and accepted methods
@mod_city.route('/<int:id>', methods=['PUT'])
@ensure_authorized
def update_city(id):
    # For PUT method
    if request.method == 'PUT':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = UpdateCityForm.from_json(request.json)

            # Validating provided data
            if form.validate():
                try:
                    # Updating the item
                    item = session.query(City).get(id)
                    if item:
                        if form.name.data is not None:
                            item.name=form.name.data
                        if form.uf.data is not None:
                            item.uf=form.uf.data
                        if form.country_id.data is not None:
                            item.country_id=form.country_id.data
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
@mod_city.route('/<int:id>', methods=['DELETE'])
@ensure_authorized
def delete_city(id):
    # For DELETE method
    if request.method == 'DELETE':
        # Creating the session for database communication
        with AppSession() as session:
            # Searching item by ID
            item = session.query(City).filter_by(id=id).first()

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
                                        "errors": _("No item found")}}), 400

# Set the route and accepted methods
@mod_country.route('', methods=['GET'])
@ensure_authenticated
def index_country():
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
        model = Country
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
@mod_country.route('', methods=['POST'])
@ensure_authorized
def create_country():
    # For POST method
    if request.method == 'POST':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = CreateCountryForm.from_json(request.json)

            # Validating provided data
            if form.validate():
                # Checking if field is already in use
                if session.query(Country).filter_by(name=form.name.data).first():
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": _("This name is already in use.")}}), 400
                try:
                    # Creating new item
                    item = Country(
                        name=form.name.data,
                        code=form.code.data,
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
@mod_country.route('/<int:id>', methods=['GET'])
@ensure_authenticated
def get_country_by_id(id):
    # For GET method
    if request.method == 'GET':
        # Creating the session for database communication
        with AppSession() as session:
            # Searching item by ID
            item = session.query(Country).get(id)

            # If item is found
            if item:
                return jsonify({"data": item.as_dict(),
                                "meta": {"success": True}})
            
            # If no item is found
            return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("No item found")}}), 400

# Set the route and accepted methods
@mod_country.route('/<int:id>', methods=['PUT'])
@ensure_authorized
def update_country(id):
    # For PUT method
    if request.method == 'PUT':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = UpdateCountryForm.from_json(request.json)

            # Validating provided data
            if form.validate():
                try:
                    # Updating the item
                    item = session.query(Country).get(id)
                    if item:
                        if form.name.data is not None:
                            if form.name.data != item.name:
                                # Checking if name is not already in use
                                if session.query(Country).filter_by(name=form.name.data).first():
                                    return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": _("This name is already in use.")}}), 400
                                else:
                                    item.name=form.name.data
                        if form.code.data is not None:
                            item.code=form.code.data
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
@mod_country.route('/<int:id>', methods=['DELETE'])
@ensure_authorized
def delete_country(id):
    # For DELETE method
    if request.method == 'DELETE':
        # Creating the session for database communication
        with AppSession() as session:
            # Searching item by ID
            item = session.query(Country).filter_by(id=id).first()

            # If the item is found
            if item:
                # Checking if there are relationships defined for the item
                if City.query.filter(City.country_id==id).first() is not None or \
                    Author.query.filter(Author.country_id==id).first() is not None or \
                    Publisher.query.filter(Publisher.country_id==id).first() is not None:
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": _("There are other items associated with this item")}}), 400
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
