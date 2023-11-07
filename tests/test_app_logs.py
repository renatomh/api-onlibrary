# -*- coding: utf-8 -*-
"""
Main testing script

"""

# Importing required models for assertion
from app.modules.users.models import User
from app.modules.log.models import Log

# Getting SQLalchemy session for the app
from app import AppSession

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


# Tests for logs management
def test_logs(client, app):
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

    # After user logs in to the server, a log must be created
    with app.app_context():
        assert Log.query.first().user_id == user["id"]

    # Creating headers to set user authorization token
    headers = {"Authorization": f"Bearer {response.json['data']['token']}"}

    # Log routes

    # Creating a new log
    response = client.post(
        "/logs",
        headers=headers,
        json={
            "model_name": "User",
            "description": "This is a log for the object",
            "model_id": user["id"],
        },
    )
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    # Saving new log
    log = response.json["data"]

    # Trying to create a log for a non existing model
    response = client.post(
        "/logs",
        headers=headers,
        json={
            "model_name": "User",
            "description": "This is a log for a non existing object",
            "model_id": -1,
        },
    )
    assert response.status_code == 400
    assert not response.json["meta"]["success"]

    # Trying to create a log for an invalid model
    response = client.post(
        "/logs",
        headers=headers,
        json={
            "model_name": "Invalid",
            "description": "This is a log for an invalid model",
            "model_id": 1,
        },
    )
    assert response.status_code == 400
    assert not response.json["meta"]["success"]

    # Deleting the created log
    response = client.delete(f'/logs/{log["id"]}', headers=headers)
    assert response.status_code == 204

    # Checking if item was deleted
    with AppSession() as session:
        assert session.query(Log).get(log["id"]) is None

    # Trying to delete an non existing log
    response = client.delete(f'/logs/{log["id"]}', headers=headers)
    assert response.status_code == 404
    assert not response.json["meta"]["success"]
