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

# Dependencies for files upload
from os import path, stat
# Function for files upload
from werkzeug.utils import secure_filename
# Library to get current timestamp
import time
# Import services
from app.services.storage import store_file, remove_file
from app.services.thumbnail import *
# Config variables
from config import UPLOAD_TEMP_FOLDER, ALLOWED_IMAGE_EXTENSIONS, tz

# Import dependencies
from datetime import datetime
import pytz

# Middlewares
from app.middleware import ensure_authenticated, ensure_authorized

# Import module forms
from app.modules.books.forms import *

# Import module models
from app.modules.books.models import *
from app.modules.settings.models import *

# Utilities functions
from app.modules.utils import get_sort_attrs, get_join_attrs, \
    get_filter_attrs

# Define the blueprint: 'auth', set its url prefix: app.url/auth
mod_author = Blueprint('authors', __name__, url_prefix='/authors')

# Set the route and accepted methods
@mod_author.route('', methods=['GET'])
@ensure_authenticated
def index_author():
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
        model = Author
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
@mod_author.route('', methods=['POST'])
@ensure_authorized
def create_author():
    # For POST method
    if request.method == 'POST':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = CreateAuthorForm.from_json(request.json)

            # Validating provided data
            if form.validate():
                # Checking if field is already in use
                if session.query(Library).filter_by(name=form.name.data).first():
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": _("This name is already in use.")}}), 400
                try:
                    # Checking if country exists
                    if form.country_id.data and session.query(Country).get(form.country_id.data) is None:
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": _("No country found")}}), 400
                    # Creating new item
                    item = Author(
                        name=form.name.data,
                        birth_date=form.birth_date.data or None,
                        death_date=form.death_date.data or None,
                        biography=form.biography.data or None,
                        external_photo_url=form.external_photo_url.data or None,
                        country_id=form.country_id.data or None,
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
@mod_author.route('/<int:id>', methods=['GET'])
@ensure_authenticated
def get_author_by_id(id):
    # For GET method
    if request.method == 'GET':
        # Creating the session for database communication
        with AppSession() as session:
            # Getting the model
            model = Author
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
@mod_author.route('/<int:id>', methods=['PUT'])
@ensure_authorized
def update_author(id):
    # For PUT method
    if request.method == 'PUT':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = UpdateAuthorForm.from_json(request.json)

            # Validating provided data
            if form.validate():
                try:
                    # Updating the item
                    item = session.query(Author).get(id)
                    if item:
                        item.name = form.name.data or item.name
                        item.birth_date = form.birth_date.data or item.birth_date
                        item.death_date = form.death_date.data or item.death_date
                        item.biography = form.biography.data or item.biography
                        item.external_photo_url = form.external_photo_url.data or item.external_photo_url
                        if form.country_id.data is not None:
                            # Checking if country exists
                            if form.country_id.data and session.query(Country).get(form.country_id.data) is None:
                                return jsonify({"data": [],
                                                "meta": {"success": False,
                                                        "errors": _("No country found")}}), 400
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
@mod_author.route('/<int:id>/photo', methods=['POST'])
@ensure_authorized
def update_author_photo(id):
    # For POST method
    if request.method == 'POST':
        # Creating the session for database communication
        with AppSession() as session:
            # If required, we can access the multipart/form-data like so:
            # form_data = dict(request.form)
            # Getting the model
            model = Author

            # If item is found
            item = session.query(model).get(id)
            if item:
                # Trying to get the photo
                try: file = request.files['photo']
                except: return jsonify({"data": {},
                                        "meta": {"success": False,
                                                "errors": _("File not sent")}}), 400

                # Setting filename with timestamp to create almost unique filename
                filename = f'{round(time.time()*1000)}-{secure_filename(file.filename)}'

                # Checking if file extension is allowed
                if ('.' in filename and filename.rsplit('.', 1)[1].lower() not in ALLOWED_IMAGE_EXTENSIONS):
                    return jsonify({"data": {},
                                    "meta": {"success": False,
                                            "errors": (_("File extension not allowed"), ALLOWED_IMAGE_EXTENSIONS)}}), 400

                # Loading to the temp folder
                file.save(path.join(UPLOAD_TEMP_FOLDER, filename))
                # Getting file size
                file_size = os.stat(path.join(UPLOAD_TEMP_FOLDER, filename)).st_size

                # Generating image thumbnail
                file_thumb = get_image_thumbnail(path.join(UPLOAD_TEMP_FOLDER, filename))
                # If the thumbnail was successfully generated
                if file_thumb is not None:
                    # We'll get the thumbnail filename
                    filename_thumb = path.basename(file_thumb)
                    # And the thumbnail file size
                    file_size_thumb = os.stat(file_thumb).st_size
                # Otherwise, we'll set the thumbnail filename and file size as None
                else:
                    filename_thumb = None
                    file_size_thumb = None

                # Calling the function to upload file to selected directory/container
                upload_response = store_file(path.join(UPLOAD_TEMP_FOLDER, filename), filename)
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

                # Removing the previous photo and thumbnail (if present)
                if item.photo_url is not None: remove_file(item.photo_url)
                if item.photo_thumbnail_url is not None: remove_file(item.photo_thumbnail_url)

                # Updating the item photo, thumbnail and meta
                item.photo_url = filename
                item.photo_file_name = file.filename
                item.photo_file_size = file_size
                item.photo_content_type = file.headers[1][1]
                item.photo_updated_at = datetime.now(tz)
                item.photo_thumbnail_url = filename_thumb
                item.photo_thumbnail_file_size = file_size_thumb
                try:
                    session.commit()
                    # Getting model and relationships data
                    data = item.as_dict()
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
                                        "errors": _("No item found")}}), 400

# Set the route and accepted methods
@mod_author.route('/<int:id>', methods=['DELETE'])
@ensure_authorized
def delete_author(id):
    # For DELETE method
    if request.method == 'DELETE':
        # Creating the session for database communication
        with AppSession() as session:
            # Searching item by ID
            item = session.query(Author).filter_by(id=id).first()

            # If the item is found
            if item:
                # Checking if there are relationships defined for the item
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
