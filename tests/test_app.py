# -*- coding: utf-8 -*-
"""
Main testing script

"""

# Importing required models for assertion
from app.modules.users.models import User

# Getting SQLalchemy session for the app
from app import AppSession

# Defining common data to be used within tests
user_registration_data = {
    'name': 'John Doe',
    'email': 'john.doe@email.com',
    'password': '123456',
    'password_confirmation': '123456',
}
user_login_data = {
    'username': 'john.doe@email.com',
    'password': '123456',
}

# Tests for user registering
def test_register(client, app):
    response = client.post('/auth/register', json=user_registration_data)
    
    # Checking response
    assert response.status_code == 200
    assert response.json['meta']['success']
    assert user_registration_data['name'] == response.json['data']['name']
    assert user_registration_data['email'] == response.json['data']['email']

    # Checking if item was created on database
    with app.app_context():
        assert User.query.count() == 1
        assert User.query.first().email == "john.doe@email.com"

    # Testing duplicated user
    response = client.post('/auth/register', json=user_registration_data)

    # Checking response
    assert response.status_code == 409
    assert not response.json['meta']['success']

# Tests for user login
def test_login(client):
    # Creating user
    client.post('/auth/register', json=user_registration_data)

    # Trying to login
    response = client.post('/auth/login', json=user_login_data)

    # Initially, it shouldn't work, since user is not active yet
    assert response.status_code == 401
    assert not response.json['meta']['success']

    # Now, we'll activate the user
    with AppSession() as session:
        session.query(User).get(1).is_active = 1
        session.commit()
    
    # We should be able to login now
    response = client.post('/auth/login', json=user_login_data)

    # Checking response
    assert response.status_code == 200
    assert response.json['meta']['success']
    assert 'token' in response.json['data']

    # Creating headers to set user authorization token
    headers = {
        'Authorization': f"Bearer {response.json['data']['token']}"
    }
    # Trying to get user's profile
    response = client.get('/profile', headers=headers)
    
    # Checking response
    assert response.status_code == 200
    assert response.json['meta']['success']
