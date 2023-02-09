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

# Dependencies for files upload
from os import path, stat
# Function for files upload
from werkzeug.utils import secure_filename
# Library to get current timestamp
import time
# Import services
from app.services.storage import store_file, remove_file
from app.services.thumbnail import get_file_thumbnail
# Config variables
from config import UPLOAD_TEMP_FOLDER, ALLOWED_FILE_EXTENSIONS, \
    tz

# Import dependencies
import pytz

# Middlewares
from app.middleware import ensure_authenticated, ensure_authorized

# Import module forms
from app.modules.document.forms import *

# Import module models
from app.modules.document.models import *
from app.modules.users.models import *
from app.modules.settings.models import *

# Utilities functions
from app.modules.utils import get_sort_attrs, get_join_attrs, \
    get_filter_attrs
from app.modules.document.utils import notify_document_expiration

# Define the blueprint: 'auth', set its url prefix: app.url/auth
mod_document_category = Blueprint('document_categories', __name__, url_prefix='/document_categories')
mod_document = Blueprint('documents', __name__, url_prefix='/documents')
mod_document_model = Blueprint('document_models', __name__, url_prefix='/document_models')
mod_document_sharing = Blueprint('document_sharings', __name__, url_prefix='/document_sharings')

# Set the route and accepted methods
@mod_document_category.route('', methods=['GET'])
@ensure_authenticated
def index_document_category():
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
        model = DocumentCategory
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
                    filter(or_(model.library_id==g.user.library_id, model.library_id==None)).\
                    order_by(*sort_attrs).paginate(page, limit, False, max_per_page)
            else:
                # If joins are not required
                res = model.query.options(selectinloads).\
                    filter(*filter_attrs).\
                    filter(or_(model.library_id==g.user.library_id, model.library_id==None)).\
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
@mod_document_category.route('', methods=['POST'])
@ensure_authorized
def create_document_category():
    # For POST method
    if request.method == 'POST':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = CreateDocumentCategoryForm.from_json(request.json)
            # Getting the model
            model = DocumentCategory

            # Validating provided data
            if form.validate():
                try:
                    # Checking if unique value is already in use
                    if session.query(model).filter_by(code=form.code.data).first():
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": _("This code is "
                                                "already in use.")}}), 400

                    # Creating new item
                    item = model(
                        code=form.code.data,
                        name=form.name.data,
                        library_id=g.user.library_id,
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
@mod_document_category.route('/<int:id>', methods=['GET'])
@ensure_authenticated
def get_document_category_by_id(id):
    # For GET method
    if request.method == 'GET':
        # Creating the session for database communication
        with AppSession() as session:
            # Getting the model
            model = DocumentCategory
            selectinloads = eval(''.join(f'selectinload({r}), ' for r in list(model.__mapper__.relationships)))
            
            # Searching item by ID
            item = session.query(model).options(selectinloads).\
                filter(or_(model.library_id==g.user.library_id, model.library_id==None)).\
                filter_by(id=id).first()

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
@mod_document_category.route('/<int:id>', methods=['PUT'])
@ensure_authorized
def update_document_category(id):
    # For PUT method
    if request.method == 'PUT':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = UpdateDocumentCategoryForm.from_json(request.json)
            # Getting the model
            model = DocumentCategory

            # Validating provided data
            if form.validate():
                try:
                    # Checking if unique value is already in use
                    other_item = session.query(model).filter_by(code=form.code.data).first()
                    if other_item and other_item.id != id:
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": _("This code is "
                                                "already in use.")}}), 400
                    # Updating the item
                    item = session.query(model).get(id)
                    if item:
                        # Checking if item library is allowed for user
                        if item.library_id and item.library_id != g.user.library_id:
                            return jsonify({"data": [],
                                            "meta": {"success": False,
                                                    "errors": _("Item library not allowed for user")}}), 400
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
@mod_document_category.route('/<int:id>', methods=['DELETE'])
@ensure_authorized
def delete_document_category(id):
    # For DELETE method
    if request.method == 'DELETE':
        # Creating the session for database communication
        with AppSession() as session:
            # Searching item by ID
            item = session.query(DocumentCategory).filter_by(id=id).first()

            # If the item is found
            if item:
                # Checking if item library is allowed for user
                if item.library_id and item.library_id != g.user.library_id:
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": _("Item library not allowed for user")}}), 400
                # Checking if there are any associated assets to the asset group
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
@mod_document.route('', methods=['GET'])
@ensure_authorized
def index_document():
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
        model = Document
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
                    filter(or_(model.library_id==g.user.library_id, model.library_id==None)).\
                    order_by(*sort_attrs).paginate(page, limit, False, max_per_page)
            else:
                # If joins are not required
                res = model.query.options(selectinloads).\
                    filter(*filter_attrs).\
                    filter(or_(model.library_id==g.user.library_id, model.library_id==None)).\
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
@mod_document.route('/my', methods=['GET'])
@ensure_authenticated
def index_my_document():
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
        model = Document
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
@mod_document.route('/shared', methods=['GET'])
@ensure_authenticated
def index_shared_document():
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
        model = Document
        selectinloads = eval(''.join(f'selectinload({r}), ' for r in list(model.__mapper__.relationships)))

        # First, we'll get a list of shared documents IDs
        res_ids = DocumentSharing.query\
            .filter(DocumentSharing.shared_user_id==g.user.id)\
            .with_entities(DocumentSharing.document_id)\
            .order_by(DocumentSharing.id.desc()).all()
        shared_document_ids = [res_id[0] for res_id in res_ids]

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
                    filter(model.id.in_(shared_document_ids)).\
                    order_by(*sort_attrs).paginate(page, limit, False, max_per_page)
            else:
                # If joins are not required
                res = model.query.options(selectinloads).\
                    filter(*filter_attrs).\
                    filter(model.id.in_(shared_document_ids)).\
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
@mod_document.route('', methods=['POST'])
@ensure_authorized
def create_document():
    # For POST method
    if request.method == 'POST':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted, we can access the multipart/form-data like so
            print(dict(request.form))
            form = CreateDocumentForm.from_json(dict(request.form))
            # Getting the model
            model = Document

            # Trying to get the file
            try: file = request.files['file']
            except: return jsonify({"data": {},
                                    "meta": {"success": False,
                                            "errors": _("File not sent")}}), 400

            # Setting filename with timestamp to create almost unique filename
            filename = f'{round(time.time()*1000)}-{secure_filename(file.filename)}'

            # If file extension is not allowed, we inform about the error
            if ('.' in filename and filename.rsplit('.', 1)[1].lower() not in ALLOWED_FILE_EXTENSIONS):
                return jsonify({"data": {},
                                "meta": {"success": False,
                                        "errors": (_("File extension not allowed"), ALLOWED_FILE_EXTENSIONS)}}), 400
            
            # Otherwise, we'll check if the other required data was provided
            # Validating provided data
            if form.validate():
                try:
                    # If no code was provided, we'll create one automatically by the timestamp
                    if form.code.data is None:
                        code = round(time.time()*1000)
                        # If code is already present
                        if session.query(model).filter_by(code=str(code)).first():
                            # We'll add code value by one, until we get a unique code
                            CODE_FLAG = True
                            while CODE_FLAG:
                                code += 1
                                if not session.query(model).filter_by(code=str(code)).first():
                                    CODE_FLAG = False
                        # Assigning code to the form data
                        form.code.data = str(code)
                    # Otherwise, we must check if code is unique
                    elif session.query(model).filter_by(code=form.code.data).first():
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": _("This code is "
                                                "already in use.")}}), 400
                    # If a document category was provided
                    if form.document_category_id.data:
                        # Checking if document category exists
                        document_category = session.query(DocumentCategory).get(form.document_category_id.data)
                        if document_category is None:
                            return jsonify({"data": [],
                                            "meta": {"success": False,
                                                    "errors": _("No document category found")}}), 400
                        # Checking if item library is allowed for user
                        if document_category.library_id and document_category.library_id != g.user.library_id:
                            return jsonify({"data": [],
                                            "meta": {"success": False,
                                                    "errors": _("Item library not allowed for user")}}), 400
                    # If an alert should be sent and no email address was provided, we'll try to use the user email
                    if int(form.alert.data) == 1 and form.alert_email.data is None:
                        # If user email is not available, we inform about the error
                        if g.user.email is None:
                            return jsonify({"data": [],
                                            "meta": {"success": False,
                                                    "errors": _("Alert email must be provided, since user has no email associated")}}), 400
                        # Otherwise, we'll use the user's email
                        form.alert_email.data = g.user.email
                    # If an alert should be sent and number of days to alert was provided, we'll inform about the error
                    if int(form.alert.data) == 1 and form.days_to_alert.data is None:
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": _("Days to alert must be provided")}}), 400

                    # Loading the file to the temp folder
                    file.save(path.join(UPLOAD_TEMP_FOLDER, filename))
                    # Getting file size
                    file_size = os.stat(path.join(UPLOAD_TEMP_FOLDER, filename)).st_size

                    # Generating file thumbnail
                    file_thumb = get_file_thumbnail(path.join(UPLOAD_TEMP_FOLDER, filename))
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

                    # Creating new item
                    item = model(
                        code=form.code.data,
                        description=form.description.data,
                        observations=form.observations.data,
                        expires_at=form.expires_at.data,
                        alert_email=form.alert_email.data,
                        alert=form.alert.data,
                        days_to_alert=form.days_to_alert.data,
                        library_id=g.user.library_id,
                        user_id=g.user.id,
                        document_category_id=form.document_category_id.data,
                        file_url=filename,
                        file_name=file.filename,
                        file_size=file_size,
                        file_content_type=file.headers[1][1],
                        file_updated_at=datetime.now(tz),
                        file_thumbnail_url=filename_thumb,
                        file_thumbnail_file_size=file_size_thumb,
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
@mod_document.route('/<int:id>', methods=['GET'])
@ensure_authenticated
def get_document_by_id(id):
    # For GET method
    if request.method == 'GET':
        # Creating the session for database communication
        with AppSession() as session:
            # Getting the model
            model = Document
            selectinloads = eval(''.join(f'selectinload({r}), ' for r in list(model.__mapper__.relationships)))
            
            # Searching item by ID
            item = session.query(model).options(selectinloads).\
                filter(or_(model.library_id==g.user.library_id, model.library_id==None)).\
                filter_by(id=id).first()

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
@mod_document.route('/<int:id>', methods=['PUT'])
@ensure_authorized
def update_document(id):
    # For PUT method
    if request.method == 'PUT':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = UpdateDocumentForm.from_json(request.json)
            # Getting the model
            model = Document

            # Validating provided data
            if form.validate():
                try:
                    # Checking if unique value is already in use
                    other_item = session.query(model).filter_by(code=form.code.data).first()
                    if other_item and other_item.id != id:
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": _("This code is "
                                                "already in use.")}}), 400
                    # Updating the item
                    item = session.query(model).get(id)
                    if item:
                        # Checking if item library is allowed for user
                        if item.library_id and item.library_id != g.user.library_id:
                            return jsonify({"data": [],
                                            "meta": {"success": False,
                                                    "errors": _("Item library not allowed for user")}}), 400
                        # If document category was provided
                        if form.document_category_id.data:
                            # Checking if document category exists
                            document_category = session.query(DocumentCategory).get(form.document_category_id.data)
                            if document_category is None:
                                return jsonify({"data": [],
                                                "meta": {"success": False,
                                                        "errors": _("No document category found")}}), 400
                            # Checking if document category belongs to the item's library
                            if document_category.library_id and item.library_id and document_category.library_id != item.library_id:
                                return jsonify({"data": [],
                                                "meta": {"success": False,
                                                        "errors": _("Document category does not belong to defined library")}}), 400
                        # If the alert was set, there must be an alert email and days to alert
                        if form.alert.data and int(form.alert.data) == 1:
                            if form.alert_email.data is None and item.alert_email is None:
                                # If user email is not available, we inform about the error
                                if g.user.email is None:
                                    return jsonify({"data": [],
                                                    "meta": {"success": False,
                                                            "errors": _("Alert email must be provided, since user has no email associated")}}), 400
                                # Otherwise, we'll use the user's email
                                form.alert_email.data = g.user.email
                            if form.days_to_alert.data is None and item.days_to_alert is None:
                                return jsonify({"data": [],
                                                "meta": {"success": False,
                                                        "errors": _("Days to alert must be provided")}}), 400
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
@mod_document.route('/<int:id>', methods=['DELETE'])
@ensure_authorized
def delete_document(id):
    # For DELETE method
    if request.method == 'DELETE':
        # Creating the session for database communication
        with AppSession() as session:
            # Searching item by ID
            item = session.query(Document).filter_by(id=id).first()

            # If the item is found
            if item:
                # Checking if item library is allowed for user
                if item.library_id and item.library_id != g.user.library_id:
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": _("Item library not allowed for user")}}), 400
                # Checking if there are any associated assets to the asset group
                # TODO: check for associated items
                try:
                    # Here we might also have to remove the files from the server
                    # So we first retrieve the file URL
                    file_url = item.file_url
                    file_thumbnail_url = item.file_thumbnail_url
                    # Removing the item
                    session.delete(item)
                    session.commit()
                    # Removing the files
                    remove_file(file_url)
                    if file_thumbnail_url is not None: remove_file(file_thumbnail_url)
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
@mod_document_model.route('', methods=['GET'])
@ensure_authenticated
def index_document_model():
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
        model = DocumentModel
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
                    order_by(*sort_attrs).paginate(page, limit, False, max_per_page)
            else:
                # If joins are not required
                res = model.query.options(selectinloads).\
                    filter(*filter_attrs).\
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
@mod_document_model.route('', methods=['POST'])
@ensure_authorized
def create_document_model():
    # For POST method
    if request.method == 'POST':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = CreateDocumentModelForm.from_json(request.json)
            # Getting the model
            model = DocumentModel

            # Validating provided data
            if form.validate():
                try:
                    # Checking if document is already associated with the model
                    if session.query(DocumentModel).filter_by(
                            model_name=form.model_name.data,
                            model_id=form.model_id.data,
                            document_id=form.document_id.data,
                        ).first():
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": _("This document is already associated to the model")}}), 400
                    # Checking if document exists
                    if session.query(Document).get(form.document_id.data) is None:
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": _("No document found")}}), 400
                    # Creating a dict with the possible model names
                    # TODO: must be updated if other models should be allowed
                    model_names = {
                        'User': User,
                    }
                    # Checking if model exists
                    if form.model_name.data in model_names.keys():
                        if model_names[form.model_name.data].query.get(form.model_id.data) is None:
                            return jsonify({"data": [],
                                            "meta": {"success": False,
                                                    "errors": _("No model found")}}), 400
                    # If model name is not valid
                    else:
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": _("Model not applicable")}}), 400
                    # Creating new item
                    item = model(
                        model_name=form.model_name.data,
                        model_id=form.model_id.data,
                        document_id=form.document_id.data,
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
@mod_document_model.route('/<int:id>', methods=['GET'])
@ensure_authenticated
def get_document_model_by_id(id):
    # For GET method
    if request.method == 'GET':
        # Creating the session for database communication
        with AppSession() as session:
            # Getting the model
            model = DocumentModel
            selectinloads = eval(''.join(f'selectinload({r}), ' for r in list(model.__mapper__.relationships)))
            
            # Searching item by ID
            item = session.query(model).options(selectinloads).filter_by(id=id).first()

            # If no item is found
            if item is None:
                return jsonify({"data": [],
                                "meta": {"success": False,
                                        "errors": _("No item found")}}), 400
            # Otherwise
            data = item.as_dict()
            # Creating a dict with the possible model names
            # TODO: must be updated if other models should be allowed
            model_names = {
                'User': User,
            }
            # Appending the model data, if a valid model name is set
            if data['model_name'] in model_names.keys():
                data['model'] = session.query(model_names[data['model_name']]).get(data['model_id']).as_dict()

            # If item is found
            if data:
                return jsonify({"data": data,
                                "meta": {"success": True}})

# Set the route and accepted methods
@mod_document_model.route('/<int:id>', methods=['DELETE'])
@ensure_authorized
def delete_document_model(id):
    # For DELETE method
    if request.method == 'DELETE':
        # Creating the session for database communication
        with AppSession() as session:
            # Searching item by ID
            item = session.query(DocumentModel).filter_by(id=id).first()

            # If the item is found
            if item:
                # Checking if there are any associated assets to the asset group
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
@mod_document_sharing.route('', methods=['GET'])
@ensure_authenticated
def index_document_sharing():
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
        model = DocumentSharing
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
                    order_by(*sort_attrs).paginate(page, limit, False, max_per_page)
            else:
                # If joins are not required
                res = model.query.options(selectinloads).\
                    filter(*filter_attrs).\
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
@mod_document.route('/<int:id>/share', methods=['POST'])
@ensure_authorized
def create_document_sharing(id):
    # For POST method
    if request.method == 'POST':
        # Creating the session for database communication
        with AppSession() as session:
            # If data form is submitted
            form = CreateDocumentSharingForm.from_json(request.json)
            # Getting the model
            model = DocumentSharing

            # Validating provided data
            if form.validate():
                try:
                    # Checking if document exists
                    document = session.query(Document).get(id)
                    if document is None:
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": _("No document found")}}), 400
                    # Checking if document belongs to user
                    if document.user_id != g.user.id:
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": _("Only the document owner can share the file")}}), 400
                    # Checking if shared user exists
                    if session.query(User).get(form.shared_user_id.data) is None:
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": _("No user found")}}), 400
                    # Checking if user is trying to share the file with himself
                    if form.shared_user_id.data == g.user.id:
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": _("You already own this file")}}), 400
                    # Checking if user is trying to reshare a document with the same user
                    if session.query(DocumentSharing).filter_by(
                            shared_user_id=form.shared_user_id.data,
                            document_id=id,
                        ).first():
                        return jsonify({"data": [],
                                        "meta": {"success": False,
                                                "errors": _("This document is already shared with the user")}}), 400
                    # Creating new item
                    item = model(
                        shared_user_id=form.shared_user_id.data,
                        document_id=id,
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
@mod_document_sharing.route('/<int:id>', methods=['GET'])
@ensure_authenticated
def get_document_sharing_by_id(id):
    # For GET method
    if request.method == 'GET':
        # Creating the session for database communication
        with AppSession() as session:
            # Getting the model
            model = DocumentSharing
            selectinloads = eval(''.join(f'selectinload({r}), ' for r in list(model.__mapper__.relationships)))
            
            # Searching item by ID
            item = session.query(model).options(selectinloads).filter_by(id=id).first()

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
@mod_document_sharing.route('/<int:id>', methods=['DELETE'])
@ensure_authorized
def delete_document_sharing(id):
    # For DELETE method
    if request.method == 'DELETE':
        # Creating the session for database communication
        with AppSession() as session:
            # Searching item by ID
            item = session.query(DocumentSharing).filter_by(id=id).first()

            # If the item is found
            if item:
                # Checking if the user is the document owner, if not, throw an error
                document = session.query(Document).get(item.document_id)
                if document.user_id != g.user.id:
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                            "errors": _("Only the document owner can stop sharing the file")}}), 400
                # Checking if there are any associated assets to the asset group
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
@mod_document.route('/<int:id>/notify_expiration', methods=['POST'])
@ensure_authorized
def notify_expiring_document(id):
    # For POST method
    if request.method == 'POST':
        # Creating the session for database communication
        with AppSession() as session:
            try:
                # Checking if document exists
                document = session.query(Document).get(id)
                if document is None:
                    return jsonify({"data": [],
                                    "meta": {"success": False,
                                             "errors": _("No document found")}}), 400

                # Trying to notify the users and email addresses about expiring document
                notify_document_expiration(id, session)

                return jsonify({"data": _("Users will be notified"),
                                "meta": {"success": True}})

            # If an error occurrs
            except Exception as e:
                session.rollback()
                return jsonify({"data": [],
                                "meta": {"success": False,
                                         "errors": str(e)}}), 500
