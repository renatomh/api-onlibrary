# -*- coding: utf-8 -*-
"""
Main testing script

"""

# Importing required models for assertion
from app.modules.users.models import User
from app.modules.notification.models import Notification

# Getting SQLalchemy session for the app
from app import AppSession

# Other dependencies
from config import tz
from datetime import datetime
import urllib
import json

# Defining common data to be used within tests
user_registration_data = {
    "name": "John Doe",
    "email": "john.doe@email.com",
    "password": "123456",
    "password_confirmation": "123456",
}
user_login_data = {
    "username": "john.doe@email.com",
    "password": "123456",
}

# Default datetime format
dt_format = "%Y-%m-%dT%H:%M:%S%z"


# Helper function to build query string from dicts
def build_query_string(params):
    # Initializing the query params
    query_params = []

    # For each key=value pair
    for key, value in params.items():
        # Handle lists by converting them to a JSON string
        if isinstance(value, list):
            value = json.dumps(value)
        query_params.append(f"{key}={urllib.parse.quote(str(value))}")

    # Returning the generated query string
    return "&".join(query_params)


# Tests for notifications management
def test_notifications(client, app):
    # Creating user
    client.post("/auth/register", json=user_registration_data)

    # Activate the user and setting its role as admin
    with AppSession() as session:
        session.query(User).get(1).is_active = 1
        session.query(User).get(1).role_id = 1
        session.commit()

    # We should be able to login now
    response = client.post("/auth/login", json=user_login_data)

    # Saving the user data
    user = response.json["data"]

    # Creating headers to set user authorization token
    headers = {"Authorization": f"Bearer {response.json['data']['token']}"}

    # Notification routes

    # Creating a new notification
    response = client.post(
        "/notifications",
        headers=headers,
        json={
            "title": "New Notification! # 001",
            "description": "A new notification has been created for you. Number: 001",
            "user_id": user["id"],
            "web_action": "/notifications/1",
            "mobile_action": "/notifications/1",
        },
    )
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    # Saving new notification
    notification = response.json["data"]

    # Trying to create a notification for a non existing user
    response = client.post(
        "/notifications",
        headers=headers,
        json={
            "title": "New Notification! # 001",
            "description": "A notification for a non existing user",
            "user_id": -1,
            "web_action": "/notifications/1",
            "mobile_action": "/notifications/1",
        },
    )
    assert response.status_code == 400
    assert not response.json["meta"]["success"]

    # Setting the created notification as read
    read_date_str = "2023-08-17T08:30:00+0000"
    response = client.put(
        f'/notifications/{notification["id"]}/read',
        headers=headers,
        json={
            "is_read": 1,
            "read_at": read_date_str,
        },
    )
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    # Checking if status is updated
    read_notification = response.json["data"]
    assert read_notification["is_read"] == 1

    # Parsing read datetimes with timezones and check if they're correct
    # We'll also parse datetime string timezones
    orig_read_date = datetime.strptime(read_date_str, dt_format).astimezone(tz)
    ret_read_date = datetime.strptime(
        read_notification["read_at"], dt_format
    ).astimezone(tz)
    assert orig_read_date == ret_read_date

    # Resetting the notification as read, without providing the read datetime
    response = client.put(
        f'/notifications/{notification["id"]}/read',
        headers=headers,
        json={
            "is_read": 1,
        },
    )
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    # Checking if status is updated
    read_notification = response.json["data"]
    assert read_notification["is_read"] == 1

    # Parsing read datetimes with timezones and check if they're correct
    # We'll also parse datetime string timezones
    curr_date = datetime.now().astimezone(tz)
    ret_read_date = datetime.strptime(
        read_notification["read_at"], dt_format
    ).astimezone(tz)
    # The current datetime and the returned one must be pretty close (e.g.: less than 10 seconds)
    assert (curr_date - ret_read_date).total_seconds() < 10

    # Setting the notification as unread
    response = client.put(
        f'/notifications/{notification["id"]}/read',
        headers=headers,
        json={
            # We must provide zero value ('0') as a string, or the form validator won't accept it
            # It would consider it to be 'null'
            "is_read": "0",
        },
    )
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    # Checking if status and read date are updated
    read_notification = response.json["data"]
    assert read_notification["is_read"] == 0
    assert read_notification["read_at"] == None

    # Deleting the created notification
    response = client.delete(f'/notifications/{notification["id"]}', headers=headers)
    assert response.status_code == 204

    # Checking if item was deleted
    with AppSession() as session:
        assert session.query(Notification).get(notification["id"]) is None

    # Trying to delete an non existing notification
    response = client.delete(f'/notifications/{notification["id"]}', headers=headers)
    assert response.status_code == 404
    assert not response.json["meta"]["success"]

    # Creating new notifications
    no_notifications = 5
    for i in range(0, 5):
        client.post(
            "/notifications",
            headers=headers,
            json={
                "title": f"New Notification! # 00{i}",
                "description": f"A new notification has been created for you. Number: 00{i}",
                "user_id": user["id"],
                "web_action": f"/notifications/{i}",
                "mobile_action": f"/notifications/{i}",
            },
        )

    # Now, we'll set all notifications as read
    client.put(
        "/notifications/read_all",
        headers=headers,
    )

    # Querying the notifications
    params = {
        "limit": 25,
        "page": 1,
        "filter": [
            {
                "property": "is_read",
                "value": 1,
                "anyMatch": True,
                "joinOn": "and",
                "operator": "==",
            },
        ],
        "sort": [
            {"property": "id", "direction": "ASC"},
        ],
        "timezone": "America/Sao_Paulo",
    }
    # Encoding the params
    query_params = build_query_string(params)
    response = client.get(f"/notifications/my?{query_params}", headers=headers)

    # Here, the correct number of items must be returned
    assert response.json["meta"]["count"] == no_notifications
    assert len(response.json["data"]) == no_notifications

    # CHecking if read datetimes are correct
    curr_date = datetime.now().astimezone(tz)
    for read_notification in response.json["data"]:
        ret_read_date = datetime.strptime(
            read_notification["read_at"], dt_format
        ).astimezone(tz)
        # The current datetime and the returned one must be pretty close (e.g.: less than 10 seconds)
        assert (curr_date - ret_read_date).total_seconds() < 10
        # Also, item must be set as read
        assert read_notification["is_read"] == 1
