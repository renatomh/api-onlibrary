"""Tests for the settings module."""

from app import AppSession
from app.modules.users.models import User
from app.modules.settings.models import UF, City

# Common data to be used within tests
USER_REGISTRATION_DATA = {
    "name": "John Doe",
    "email": "john.doe@email.com",
    "password": "123456",
    "password_confirmation": "123456",
}
USER_LOGIN_DATA = {
    "username": "john.doe@email.com",
    "password": "123456",
}
UFS_DATA = [
    {
        "code": "UF1",
        "name": "Unidade Federativa 1",
    },
    {
        "code": "UF2",
        "name": "Unidade Federativa 2",
    },
]
CITIES_DATA = [
    {
        "name": "City 1",
        "uf_id": 1,
    },
    {
        "name": "City 2",
        "uf_id": 2,
    },
]


def test_ufs(client):
    """Tests for UFs management."""

    # Creating user
    client.post("/auth/register", json=USER_REGISTRATION_DATA)

    # Activate the user and setting its role as admin
    with AppSession() as session:
        session.query(User).get(1).is_active = 1
        session.query(User).get(1).role_id = 1
        session.commit()

    # We should be able to login now
    response = client.post("/auth/login", json=USER_LOGIN_DATA)

    # Creating headers to set user authorization token
    headers = {"Authorization": f"Bearer {response.json['data']['token']}"}

    # UF routes

    # Creating a new UF
    response = client.post(
        "/ufs",
        headers=headers,
        json=UFS_DATA[0],
    )
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    # Saving new item
    uf1 = response.json["data"]

    # Trying to create a new UF with an already existing code
    response = client.post(
        "/ufs",
        headers=headers,
        json={
            "code": uf1["code"],
            "name": uf1["name"],
        },
    )
    assert response.status_code == 400
    assert not response.json["meta"]["success"]

    # Creating another UF
    response = client.post(
        "/ufs",
        headers=headers,
        json=UFS_DATA[1],
    )
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    # Saving new item
    uf2 = response.json["data"]

    # Updating the created UF
    response = client.put(
        f'/ufs/{uf1["id"]}',
        headers=headers,
        json={
            "code": "Updated Code",
            "name": "Updated Name",
        },
    )
    assert response.status_code == 200
    assert response.json["meta"]["success"]

    # Updating the first created UF with a repeated UF's code
    response = client.put(
        f'/ufs/{uf1["id"]}',
        headers=headers,
        json={
            "code": uf2["code"],
            "name": uf2["name"],
        },
    )
    assert response.status_code == 400
    assert not response.json["meta"]["success"]

    # Deleting the created UF
    response = client.delete(f'/ufs/{uf1["id"]}', headers=headers)
    assert response.status_code == 204

    # Checking if item was deleted
    with AppSession() as session:
        assert session.query(UF).get(uf1["id"]) is None

    # Trying to delete an non existing UF
    response = client.delete(f'/ufs/{uf1["id"]}', headers=headers)
    assert response.status_code == 404
    assert not response.json["meta"]["success"]


def test_cities(client):
    """Tests for cities management."""

    # Creating user
    client.post("/auth/register", json=USER_REGISTRATION_DATA)

    # Activate the user and setting its role as admin
    with AppSession() as session:
        session.query(User).get(1).is_active = 1
        session.query(User).get(1).role_id = 1
        session.commit()

    # We should be able to login now
    response = client.post("/auth/login", json=USER_LOGIN_DATA)

    # Creating headers to set user authorization token
    headers = {"Authorization": f"Bearer {response.json['data']['token']}"}

    # City routes

    # Creating a new city
    response = client.post(
        "/cities",
        headers=headers,
        json=CITIES_DATA[0],
    )
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    # Saving new item
    city1 = response.json["data"]

    # Trying to create a new city with a non existing UF ID
    response = client.post(
        "/cities",
        headers=headers,
        json={
            "name": city1["name"],
            "uf_id": -1,
        },
    )
    assert response.status_code == 404
    assert not response.json["meta"]["success"]

    # Creating another city
    response = client.post(
        "/cities",
        headers=headers,
        json=CITIES_DATA[1],
    )
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    # Saving new item
    city2 = response.json["data"]

    # Updating the created city
    response = client.put(
        f'/cities/{city1["id"]}',
        headers=headers,
        json={
            "name": "Updated Name",
            "uf_id": 2,
        },
    )
    assert response.status_code == 200
    assert response.json["meta"]["success"]

    # Updating the first created city with a repeated city's name (it should be possible)
    response = client.put(
        f'/cities/{city1["id"]}',
        headers=headers,
        json={
            "name": city2["name"],
            "uf_id": city2["uf_id"],
        },
    )
    assert response.status_code == 200
    assert response.json["meta"]["success"]

    # Deleting the created city
    response = client.delete(f'/cities/{city1["id"]}', headers=headers)
    assert response.status_code == 204

    # Checking if item was deleted
    with AppSession() as session:
        assert session.query(City).get(city1["id"]) is None

    # Trying to delete an non existing city
    response = client.delete(f'/cities/{city1["id"]}', headers=headers)
    assert response.status_code == 404
    assert not response.json["meta"]["success"]
