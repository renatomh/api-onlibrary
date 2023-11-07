# -*- coding: utf-8 -*-
"""
Main testing script

"""

# Importing required models for assertion
from app.modules.users.models import User, Role

# Getting SQLalchemy session for the app
from app import AppSession

# Other dependencies
import os

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


# Tests for user registering
def test_register(client, app):
    response = client.post("/auth/register", json=user_registration_data)

    # Checking response
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    assert user_registration_data["name"] == response.json["data"]["name"]
    assert user_registration_data["email"] == response.json["data"]["email"]

    # Checking if item was created on database
    with app.app_context():
        assert User.query.count() == 1
        assert User.query.first().email == "john.doe@email.com"

    # Testing duplicated user
    response = client.post("/auth/register", json=user_registration_data)

    # Checking response
    assert response.status_code == 409
    assert not response.json["meta"]["success"]


# Tests for user login
def test_login(client):
    # Creating user
    client.post("/auth/register", json=user_registration_data)

    # Trying to login
    response = client.post("/auth/login", json=user_login_data)

    # Initially, it shouldn't work, since user is not active yet
    assert response.status_code == 401
    assert not response.json["meta"]["success"]

    # Now, we'll activate the user
    with AppSession() as session:
        session.query(User).get(1).is_active = 1
        session.commit()

    # We should be able to login now
    response = client.post("/auth/login", json=user_login_data)

    # Checking response
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    assert "token" in response.json["data"]

    # Creating headers to set user authorization token
    headers = {"Authorization": f"Bearer {response.json['data']['token']}"}
    # Trying to get user's profile
    response = client.get("/profile", headers=headers)

    # Checking response
    assert response.status_code == 200
    assert response.json["meta"]["success"]


# Tests for user profile
def test_profile(client):
    # Creating user
    client.post("/auth/register", json=user_registration_data)

    # Trying to login
    response = client.post("/auth/login", json=user_login_data)

    # Initially, it shouldn't work, since user is not active yet
    assert response.status_code == 401
    assert not response.json["meta"]["success"]

    # Now, we'll activate the user
    with AppSession() as session:
        session.query(User).get(1).is_active = 1
        session.commit()

    # We should be able to login now
    response = client.post("/auth/login", json=user_login_data)

    # Checking response
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    assert "token" in response.json["data"]

    # Creating headers to set user authorization token
    headers = {"Authorization": f"Bearer {response.json['data']['token']}"}
    # Trying to get user's profile
    response = client.get("/profile", headers=headers)

    # Checking response
    assert response.status_code == 200
    assert response.json["meta"]["success"]

    # Trying to update the user's avatar with not allowed file extension
    with open("tests/assets/profile.jpg", "rb") as file:
        response = client.post(
            "/profile/avatar",
            headers=headers,
            data={"avatar": (file, "profile.notallowed")},
        )
    assert response.status_code == 400
    assert response.json["meta"]["success"] is False

    # Trying to update the user's avatar with allowed file extension
    with open("tests/assets/profile.jpg", "rb") as file:
        response = client.post(
            "/profile/avatar", headers=headers, data={"avatar": (file, "profile.jpg")}
        )
    assert response.status_code == 200
    assert response.json["meta"]["success"] is True

    # Getting the user data
    with AppSession() as session:
        user = session.query(User).get(response.json["data"]["id"])
        # Getting parent's directory
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Checking if files (avatar and thumbnail) were created
        assert os.path.exists(f"{parent_dir}/uploads/{user.avatar_url}")
        assert os.path.exists(f"{parent_dir}/uploads/{user.avatar_thumbnail_url}")
        # Now, we'll remove the uploaded files
        os.remove(f"{parent_dir}/uploads/{user.avatar_url}")
        os.remove(f"{parent_dir}/uploads/{user.avatar_thumbnail_url}")

    # Trying to update user's profile
    response = client.put(
        "/profile",
        headers=headers,
        json={
            "name": "Mr. John Doe",
            "username": "doe.john",
        },
    )
    assert response.status_code == 200
    response.json["data"]["name"] == "Mr. John Doe"
    response.json["data"]["username"] == "doe.john"
    assert response.json["meta"]["success"] is True


# Tests for roles management
def test_roles(client):
    # Creating user
    client.post("/auth/register", json=user_registration_data)

    # Activate the user and setting its role as admin
    with AppSession() as session:
        session.query(User).get(1).is_active = 1
        session.query(User).get(1).role_id = 1
        session.commit()

    # We should be able to login now
    response = client.post("/auth/login", json=user_login_data)

    # Creating headers to set user authorization token
    headers = {"Authorization": f"Bearer {response.json['data']['token']}"}

    # Role routes

    # Creating a new role
    response = client.post(
        "/roles",
        headers=headers,
        json={
            "name": "Test Role",
        },
    )
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    # Saving new role
    role = response.json["data"]

    # Adding routes to the newly created role
    response = client.post(
        "/role_api_routes",
        headers=headers,
        json={"route": "/profile", "method": "GET", "role_id": role["id"]},
    )
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    response = client.post(
        "/role_web_actions",
        headers=headers,
        json={"action": "/profile", "role_id": role["id"]},
    )
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    response = client.post(
        "/role_mobile_actions",
        headers=headers,
        json={"action": "/profile", "role_id": role["id"]},
    )
    assert response.status_code == 200
    assert response.json["meta"]["success"]

    # Duplicating (copying) the created role
    response = client.post(
        f'/roles/{role["id"]}/copy',
        headers=headers,
        json={
            "name": "Duplicated Test Role",
        },
    )
    assert response.status_code == 200
    assert response.json["meta"]["success"]

    # Updating the created role name
    response = client.put(
        f'/roles/{role["id"]}',
        headers=headers,
        json={
            "name": "Updated Test Role",
        },
    )
    assert response.status_code == 200
    assert response.json["meta"]["success"]

    # Deleting the original created role
    response = client.delete(f'/roles/{role["id"]}', headers=headers)
    assert response.status_code == 204

    # Checking if item was deleted
    with AppSession() as session:
        assert session.query(Role).get(role["id"]) is None

    # Trying to delete an non existing role
    response = client.delete(f'/roles/{role["id"]}', headers=headers)
    assert response.status_code == 404
    assert not response.json["meta"]["success"]
