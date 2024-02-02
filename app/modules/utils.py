# -*- coding: utf-8 -*-

# Import dependencies
import ast
import re

# JSON parsing
import json

# Dependencies for custom wtforms validator
from wtforms.validators import ValidationError
from wtforms import widgets, Field
from datetime import datetime

# Getting config variables
from config import tz

# SQLAlchemy dependencies
from sqlalchemy import or_

# Logging
import logging

# Importing the modules models
from app.modules.users.models import *
from app.modules.notification.models import *
from app.modules.settings.models import *
from app.modules.document.models import *
from app.modules.log.models import *


# Function to get a model relationships
def get_model_relationships(model):
    # Getting the list of relationships in the model
    model_relationships = {}
    for r in list(model.__mapper__.relationships):
        # Getting the model attribute name
        model_attr = str(r).replace(model.__name__ + ".", "")
        # Getting the related models
        # Checking if it's a many-to-many relationship or not
        if not r.__dict__["uselist"]:
            model_relationships[model_attr] = {
                "model": eval(r.entity.class_.__name__),
                "kind": "one",
            }
        else:
            model_relationships[model_attr] = {
                "model": r.__dict__["secondary"],
                "kind": "many",
            }
    return model_relationships


# Function to get the sorting attributes for a call
def get_sort_attrs(model, sort):
    # If no sorting attributes were provided, we'll use the 'id' by default
    if sort == '"[]"':
        sort = '[{"property": "id", "direction": "ASC"}]'

    # Getting the model relationships
    model_relationships = get_model_relationships(model)

    # Retrieving the sorting attributes
    sort_attrs = []
    for s in json.loads(sort):
        # Initizaling the sort model as the query model and the property name
        sort_model = model
        property = s["property"]

        # Here we check if the property is from the model or a relationship
        if "." in s["property"]:
            # If it refers to a relationship property, we need to select the model where to get the attrs from
            input_relationship = s["property"].split(".")[0]

            # For a one-to-many relationship
            if model_relationships[input_relationship]["kind"] == "one":
                sort_model = model_relationships[input_relationship]["model"]

            # For a many-to-many relationship
            elif model_relationships[input_relationship]["kind"] == "many":
                sort_model = model_relationships[input_relationship]["model"].c

            # Correcting the property name (removing the 'relationship.' from the beggining)
            property = s["property"].split(".")[1]

        sort_attrs.append(
            getattr(getattr(sort_model, property), s["direction"].lower())()
        )
    return sort_attrs


# Function to get the join attributes/relationships for a call
def get_join_attrs(model, filter, sort):
    # If no filtering or sorting attributes were provided, we'll use default values
    if filter == '"[]"':
        filter = '[{"property":"id","value":"","anyMatch":true,"joinOn":"and","operator":"like"}]'
    if sort == '"[]"':
        sort = '[{"property": "id", "direction": "ASC"}]'

    # Getting the model relationships
    model_relationships = get_model_relationships(model)
    # Retrieving the join attributes
    join_attrs = []
    # Joins required by filters
    for f in json.loads(filter):
        # First of all, we check if the property is from the model or a relationship
        if "." in f["property"]:
            # If it belongs to a relationship property
            input_relationship = f["property"].split(".")[0]
            if input_relationship in model_relationships.keys():
                # We add it to the join list if not already present
                if model_relationships[input_relationship]["model"] not in join_attrs:
                    join_attrs.append(model_relationships[input_relationship]["model"])
    # Joins required by sorting
    for s in json.loads(sort):
        # First of all, we check if the property is from the model or a relationship
        if "." in s["property"]:
            # If it belongs to a relationship property
            input_relationship = s["property"].split(".")[0]
            if input_relationship in model_relationships.keys():
                # We add it to the join list if not already present
                if model_relationships[input_relationship]["model"] not in join_attrs:
                    join_attrs.append(model_relationships[input_relationship]["model"])
    return join_attrs


# Function to check for datetime object/strings
def format_filter_parameter(object, timezone=tz):
    # If the string is formatted as a datetime
    try:
        # We'll get the datetime on specified timezone
        datetime_ptz = timezone.localize(datetime.strptime(object, "%Y-%m-%d %H:%M:%S"))
        # Convert the datetime to the system timezone
        datetime_stz = datetime_ptz.astimezone(tz)
        # And return the formatted item
        return datetime_stz.strftime("%Y-%m-%d %H:%M:%S")
    except:
        # Otherwise, we'll return the raw object
        return object


# Function to get the filtering attributes for a call
def get_filter_attrs(model, filter, timezone=tz):
    # If no filtering attributes were provided, we'll make it empty by default
    if filter == '"[]"':
        filter = '[{"property":"id","value":"","anyMatch":true,"joinOn":"and","operator":"like"}]'

    # Getting the model relationships
    model_relationships = get_model_relationships(model)

    # Retrieving the 'and' filtering attributes
    and_filter_attrs = []
    # Retrieving the 'or' filtering attributes
    or_filter_attrs = []

    # For each property to be filtered
    for f in json.loads(filter):
        # Initizaling the filter model as the query model and the property name
        filter_model = model
        property = f["property"]

        # Checking if the join will be on 'and' or 'or' (by default, it will be on 'and')
        join_on = f.get("joinOn", "and").lower()
        # Verifying if 'joinOn' option is valid
        if join_on not in ("or", "and"):
            raise Exception(f"Invalid '{join_on}' as 'joinOn' option ('or', 'and').")

        # First of all, we check if the property is from the model or a relationship
        if "." in f["property"]:
            # If it refers to a relationship property, we need to select the model where to get the attrs from
            input_relationship = f["property"].split(".")[0]

            # For a one-to-many relationship
            if model_relationships[input_relationship]["kind"] == "one":
                filter_model = model_relationships[input_relationship]["model"]

            # For a many-to-many relationship
            elif model_relationships[input_relationship]["kind"] == "many":
                filter_model = model_relationships[input_relationship]["model"].c

            # Correcting the property name (removing the 'relationship.' from the beggining)
            property = f["property"].split(".")[1]

        # Now we create the filters
        # 'Like'/'Ilike'/'Not Like'/'Not Ilike' operator
        if f["operator"].lower() in ["like", "ilike", "notlike", "notilike"]:
            # Getting the value for the property
            value = f.get("value", "")
            # Formatting to localize datetime
            value = format_filter_parameter(value, timezone)

            # If it was set to anyMatch (it could be in the middle of a string)
            if f.get("anyMatch", True):
                value = f"%{f['value']}%"

            # Appending the item to the filters
            if join_on == "and":
                and_filter_attrs.append(
                    getattr(getattr(filter_model, property), f["operator"].lower())(
                        value
                    )
                )
            elif join_on == "or":
                or_filter_attrs.append(
                    getattr(getattr(filter_model, property), f["operator"].lower())(
                        value
                    )
                )

        # Logical operators
        if f["operator"].lower() == "==":
            if join_on == "and":
                and_filter_attrs.append(
                    getattr(filter_model, property)
                    == format_filter_parameter(f["value"], timezone)
                )
            elif join_on == "or":
                or_filter_attrs.append(
                    getattr(filter_model, property)
                    == format_filter_parameter(f["value"], timezone)
                )
        if f["operator"].lower() == "!=":
            if join_on == "and":
                and_filter_attrs.append(
                    getattr(filter_model, property)
                    != format_filter_parameter(f["value"], timezone)
                )
            elif join_on == "or":
                or_filter_attrs.append(
                    getattr(filter_model, property)
                    != format_filter_parameter(f["value"], timezone)
                )
        if f["operator"].lower() == "<":
            if join_on == "and":
                and_filter_attrs.append(
                    getattr(filter_model, property)
                    < format_filter_parameter(f["value"], timezone)
                )
            elif join_on == "or":
                or_filter_attrs.append(
                    getattr(filter_model, property)
                    < format_filter_parameter(f["value"], timezone)
                )
        if f["operator"].lower() == "<=":
            if join_on == "and":
                and_filter_attrs.append(
                    getattr(filter_model, property)
                    <= format_filter_parameter(f["value"], timezone)
                )
            elif join_on == "or":
                or_filter_attrs.append(
                    getattr(filter_model, property)
                    <= format_filter_parameter(f["value"], timezone)
                )
        if f["operator"].lower() == ">":
            if join_on == "and":
                and_filter_attrs.append(
                    getattr(filter_model, property)
                    > format_filter_parameter(f["value"], timezone)
                )
            elif join_on == "or":
                or_filter_attrs.append(
                    getattr(filter_model, property)
                    > format_filter_parameter(f["value"], timezone)
                )
        if f["operator"].lower() == ">=":
            if join_on == "and":
                and_filter_attrs.append(
                    getattr(filter_model, property)
                    >= format_filter_parameter(f["value"], timezone)
                )
            elif join_on == "or":
                or_filter_attrs.append(
                    getattr(filter_model, property)
                    >= format_filter_parameter(f["value"], timezone)
                )

        # 'In' operator
        if f["operator"].lower() == "in":
            # Getting the list of values and checking for datetime items
            raw_value = ast.literal_eval(f["value"])
            value = [format_filter_parameter(v, timezone) for v in raw_value]
            if join_on == "and":
                and_filter_attrs.append(
                    getattr(getattr(filter_model, property), "in_")(value)
                )
            elif join_on == "or":
                or_filter_attrs.append(
                    getattr(getattr(filter_model, property), "in_")(value)
                )

        # 'Not In' operator
        if f["operator"].lower() == "not_in":
            # Getting the list of values and checking for datetime items
            raw_value = ast.literal_eval(f["value"])
            value = [format_filter_parameter(v, timezone) for v in raw_value]
            if join_on == "and":
                and_filter_attrs.append(
                    getattr(getattr(filter_model, property), "not_in")(value)
                )
            elif join_on == "or":
                or_filter_attrs.append(
                    getattr(getattr(filter_model, property), "not_in")(value)
                )

        # 'Between' dates operator
        if f["operator"].lower() == "between":
            value = ast.literal_eval(f["value"])
            if join_on == "and":
                and_filter_attrs.append(
                    getattr(getattr(filter_model, property), "between")(
                        format_filter_parameter(value[0], timezone),
                        format_filter_parameter(value[1], timezone),
                    )
                )
            elif join_on == "or":
                or_filter_attrs.append(
                    getattr(getattr(filter_model, property), "between")(
                        format_filter_parameter(value[0], timezone),
                        format_filter_parameter(value[1], timezone),
                    )
                )

    # Now, the two filtering attributes list must be concatenated
    filter_attrs = []
    # Extending for the 'and' filters
    if len(and_filter_attrs) > 0:
        filter_attrs.extend(and_filter_attrs)
    # Extending for the 'or' filters
    if len(or_filter_attrs) > 0:
        filter_attrs.append(or_(*or_filter_attrs))

    # Returning the obtained filters
    return filter_attrs


# Function to append data to log files
def log(file, message, level, log_format=None):
    # Creating a new file handler
    info_log = logging.FileHandler(file)
    # If no log format was provided, we use a default one
    if log_format is None:
        log_format = logging.Formatter(
            "%(asctime)s [%(levelname)s]: %(message)s",
            "%Y-%m-%d %H:%M:%S",  # Datetime format
        )
    # Setting te defined format
    info_log.setFormatter(log_format)
    # Creating the logger for the file
    logger = logging.getLogger(file)
    # Setting a threshold for the levels to be logged
    logger.setLevel(level)

    # If there's not logger handler
    if not logger.handlers:
        # Adding a new handler
        logger.addHandler(info_log)
        # And appending the message with the level set
        if level == logging.DEBUG:
            logger.debug(message)
        elif level == logging.INFO:
            logger.info(message)
        elif level == logging.WARNING:
            logger.warning(message)
        elif level == logging.ERROR:
            logger.error(message)
        elif level == logging.CRITICAL:
            logger.critical(message)

    # Closing and removing the handler
    info_log.close()
    logger.removeHandler(info_log)

    # Returning the function
    return


# Custom wtforms required conditional field
class RequiredIf(object):
    def __init__(self, message=None, **kwargs):
        self.conditions = kwargs
        self.message = message

    def __call__(self, form, field):
        current_value = form.data.get(field.name)
        if current_value is None:
            for condition_field, reserved_value in self.conditions.items():
                dependent_value = form.data.get(condition_field)
                if condition_field not in form.data:
                    continue
                elif dependent_value == reserved_value:
                    message = self.message
                    if message:
                        raise ValidationError(message)
                    else:
                        message = f"Field required when '{condition_field}' equals to '{dependent_value}'."
                    raise ValidationError(message)


# Custom wtforms 'DateTimeField' validator, which checks for data type
class DateTimeField(Field):
    """
    A text field which stores a `datetime.datetime` matching a format.
    """

    widget = widgets.TextInput()

    def __init__(
        self, label=None, validators=None, format="%Y-%m-%d %H:%M:%S", **kwargs
    ):
        super(DateTimeField, self).__init__(label, validators, **kwargs)
        self.format = format

    def _value(self):
        if self.raw_data:
            return " ".join(self.raw_data)
        else:
            return self.data and self.data.strftime(self.format) or ""

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                # Must be within the try/except
                date_str = " ".join(valuelist)
            except:
                raise ValueError(self.gettext("Not a valid datetime value"))
            try:
                # Checking which format was provided
                if self.format == "%Y-%m-%dT%H:%M:%S%z":
                    self.data = datetime.strptime(date_str, self.format).astimezone(tz)
                else:
                    self.data = datetime.strptime(date_str, self.format)
            except ValueError:
                self.data = None
                raise ValueError(self.gettext("Not a valid datetime value"))


# Custom wtforms 'DateField' validator, which checks for data type
class DateField(DateTimeField):
    """
    Same as DateTimeField, except stores a `datetime.date`.
    """

    def __init__(self, label=None, validators=None, format="%Y-%m-%d", **kwargs):
        super(DateField, self).__init__(label, validators, format, **kwargs)

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                # Must be within the try/except
                date_str = " ".join(valuelist)
            except:
                raise ValueError(self.gettext("Not a valid date value"))
            try:
                self.data = datetime.strptime(date_str, self.format).date()
            except ValueError:
                self.data = None
                raise ValueError(self.gettext("Not a valid date value"))


# Custom wtforms 'TimeField' validator, which checks for data type
class TimeField(DateTimeField):
    """
    Same as DateTimeField, except stores a `time`.
    """

    def __init__(self, label=None, validators=None, format="%H:%M", **kwargs):
        super(TimeField, self).__init__(label, validators, format, **kwargs)

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                # Must be within the try/except
                time_str = " ".join(valuelist)
            except:
                raise ValueError(self.gettext("Not a valid time value"))
            try:
                self.data = datetime.strptime(time_str, self.format).time()
            except ValueError:
                self.data = None
                raise ValueError(self.gettext("Not a valid time value"))
