"""Tests for the documents module."""

import os

from app import AppSession
from app.modules.users.models import User
from app.modules.document.models import Document, DocumentCategory


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
DOCUMENT_CATEGORIES_DATA = [
    {
        "code": "DC-01",
        "name": "Document Category 01",
    },
    {
        "code": "DC-02",
        "name": "Document Category 02",
    },
    {
        "code": "DC-03",
        "name": "Document Category 03",
    },
]
SHARE_USER_DATA = {
    "name": "Jack Dan",
    "username": "jack.dan",
    "password": "123456",
    "password_confirmation": "123456",
    "role_id": 1,
    "is_active": 1,
    "email": "jack.dan@email.com",
}


def test_document_categories(client):
    """Tests for document categories management."""

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

    # Creating a new document category
    response = client.post(
        "/document-categories", headers=headers, json=DOCUMENT_CATEGORIES_DATA[0]
    )
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    document_category1 = response.json["data"]

    # Trying to create a new document category with an already existing code
    response = client.post(
        "/document-categories",
        headers=headers,
        json={
            "code": document_category1["code"],
            "name": document_category1["name"],
        },
    )
    assert response.status_code == 400
    assert not response.json["meta"]["success"]

    # Creating another document category
    response = client.post(
        "/document-categories", headers=headers, json=DOCUMENT_CATEGORIES_DATA[1]
    )
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    document_category2 = response.json["data"]

    # Updating the created document category
    response = client.put(
        f'/document-categories/{document_category1["id"]}',
        headers=headers,
        json={
            "code": "Updated DC Code",
            "name": "Updated DC Name",
        },
    )
    assert response.status_code == 200
    assert response.json["meta"]["success"]

    # Updating the first created document category with a repeated document category's code
    response = client.put(
        f'/document-categories/{document_category1["id"]}',
        headers=headers,
        json={
            "code": document_category2["code"],
            "name": document_category2["name"],
        },
    )
    assert response.status_code == 400
    assert not response.json["meta"]["success"]

    # Deleting the created document category
    response = client.delete(
        f'/document-categories/{document_category1["id"]}', headers=headers
    )
    assert response.status_code == 204

    # Checking if item was deleted
    with AppSession() as session:
        assert session.query(DocumentCategory).get(document_category1["id"]) is None

    # Trying to delete an non existing document category
    response = client.delete(
        f'/document-categories/{document_category1["id"]}', headers=headers
    )
    assert response.status_code == 404
    assert not response.json["meta"]["success"]


def test_documents(client):
    """Tests for documents management."""

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

    # Creating some test document categories
    test_document_categories = []
    for document_category_data in DOCUMENT_CATEGORIES_DATA:
        response = client.post(
            "/document-categories", headers=headers, json=document_category_data
        )
        assert response.status_code == 200
        assert response.json["meta"]["success"]
        # Saving created document category
        test_document_categories.append(response.json["data"])

    # Document routes

    # Creating a new document with an image file
    with open("tests/assets/sample.png", "rb") as file:
        response = client.post(
            "/documents",
            headers=headers,
            data={
                "file": (file, "sample.png"),
                "code": "IMG-DOC",
                "description": "Image document",
                "observations": "The document contains an image file",
                "expires_at": "2023-12-01",
                "alert_email": "alert@email.com",
                "alert": 1,
                "days_to_alert": 7,
                "document_category_id": test_document_categories[0]["id"],
            },
        )
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    # Getting the document data
    with AppSession() as session:
        document = session.query(Document).get(response.json["data"]["id"])
        # Getting parent's directory
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Checking if files were created
        assert os.path.exists(f"{parent_dir}/uploads/{document.file_url}")
        assert os.path.exists(f"{parent_dir}/uploads/{document.file_thumbnail_url}")

    # Creating a new document with a PDF file
    with open("tests/assets/document.pdf", "rb") as file:
        response = client.post(
            "/documents",
            headers=headers,
            data={
                "file": (file, "document.pdf"),
                "code": "PDF-DOC",
                "description": "PDF document",
                "observations": "The document contains a PDF file",
                "expires_at": "2023-12-01",
                "alert_email": "alert@email.com",
                "alert": 1,
                "days_to_alert": 7,
                "document_category_id": test_document_categories[0]["id"],
            },
        )
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    # Getting the document data
    with AppSession() as session:
        document = session.query(Document).get(response.json["data"]["id"])
        # Getting parent's directory
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Checking if files were created
        assert os.path.exists(f"{parent_dir}/uploads/{document.file_url}")
        assert os.path.exists(f"{parent_dir}/uploads/{document.file_thumbnail_url}")

    # Creating a new document with a video file
    with open("tests/assets/video.mp4", "rb") as file:
        response = client.post(
            "/documents",
            headers=headers,
            data={
                "file": (file, "video.mp4"),
                "code": "VID-DOC",
                "description": "Video document",
                "observations": "The document contains a video file",
                "expires_at": "2023-12-01",
                "alert_email": "alert@email.com",
                "alert": 1,
                "days_to_alert": 7,
                "document_category_id": test_document_categories[0]["id"],
            },
        )
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    # Getting the document data
    with AppSession() as session:
        document = session.query(Document).get(response.json["data"]["id"])
        # Getting parent's directory
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Checking if files were created
        assert os.path.exists(f"{parent_dir}/uploads/{document.file_url}")
        # If FFMPEG is available, a thumbnail should be created
        if os.path.exists(os.environ["FFMPEG_PATH"]):
            assert os.path.exists(f"{parent_dir}/uploads/{document.file_thumbnail_url}")

    # Creating a new document with a text file
    with open("tests/assets/file.txt", "rb") as file:
        response = client.post(
            "/documents",
            headers=headers,
            data={
                "file": (file, "file.txt"),
                "code": "TXT-DOC",
                "description": "Text document",
                "observations": "The document contains a text file",
                "expires_at": "2023-12-01",
                "alert_email": "alert@email.com",
                "alert": 1,
                "days_to_alert": 7,
                "document_category_id": test_document_categories[0]["id"],
            },
        )
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    # Getting the document data
    with AppSession() as session:
        document = session.query(Document).get(response.json["data"]["id"])
        # Getting parent's directory
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Checking if files were created
        assert os.path.exists(f"{parent_dir}/uploads/{document.file_url}")
        # The thumbnail creation is not available for this file format

    # Trying to create a new document with an unsupported file extension
    with open("tests/assets/file.txt", "rb") as file:
        response = client.post(
            "/documents",
            headers=headers,
            data={
                "file": (file, "file.notallowed"),
                "code": "UNSUPPORTED-DOC",
                "description": "Unsupported document",
                "observations": "The document contains a unsupported file",
                "expires_at": "2023-12-01",
                "alert_email": "alert@email.com",
                "alert": 1,
                "days_to_alert": 7,
                "document_category_id": test_document_categories[0]["id"],
            },
        )
    assert response.status_code == 400
    assert not response.json["meta"]["success"]

    # Trying to create a new document with an already existing code
    with open("tests/assets/file.txt", "rb") as file:
        response = client.post(
            "/documents",
            headers=headers,
            data={
                "file": (file, "file.txt"),
                "code": "TXT-DOC",
                "description": "Repeated text document",
                "observations": "The document contains a text file with duplicate code",
                "expires_at": "2023-12-01",
                "alert_email": "alert@email.com",
                "alert": 1,
                "days_to_alert": 7,
                "document_category_id": 1,
            },
        )
    assert response.status_code == 400
    assert not response.json["meta"]["success"]

    # Trying to create new documents with invalid data fields
    # Description missing
    with open("tests/assets/file.txt", "rb") as file:
        response = client.post(
            "/documents",
            headers=headers,
            data={
                "file": (file, "file.txt"),
            },
        )
    assert response.status_code == 400
    assert not response.json["meta"]["success"]
    # Email alert flag missing
    with open("tests/assets/file.txt", "rb") as file:
        response = client.post(
            "/documents",
            headers=headers,
            data={
                "file": (file, "file.txt"),
                "description": "Document description",
            },
        )
    assert response.status_code == 400
    assert not response.json["meta"]["success"]
    # Non existing document category
    with open("tests/assets/file.txt", "rb") as file:
        response = client.post(
            "/documents",
            headers=headers,
            data={
                "file": (file, "file.txt"),
                "description": "Document description",
                "alert": 0,
                "document_category_id": -1,
            },
        )
    assert response.status_code == 400
    assert not response.json["meta"]["success"]
    # Email alert without days to alert
    with open("tests/assets/file.txt", "rb") as file:
        response = client.post(
            "/documents",
            headers=headers,
            data={
                "file": (file, "file.txt"),
                "description": "Document description",
                "alert": 1,
            },
        )
    assert response.status_code == 400
    assert not response.json["meta"]["success"]

    # Updating a created document
    response = client.put(
        "/documents/1",
        headers=headers,
        json={
            "description": "This is the updated document description",
        },
    )
    assert response.status_code == 200
    assert response.json["meta"]["success"]

    # Trying to update a document with a duplicated code
    response = client.put(
        "/documents/1",
        headers=headers,
        json={
            "code": "PDF-DOC",
        },
    )
    assert response.status_code == 400
    assert not response.json["meta"]["success"]

    # Here, we'll try to delete a document category which has a document associated to it
    # To check if it will fail
    response = client.delete(
        f'/document-categories/{test_document_categories[0]["id"]}', headers=headers
    )
    assert response.status_code == 400
    assert not response.json["meta"]["success"]

    # Now, we'll remove all the created documents (to remove uploaded files)
    # First we list the created dcuments
    response = client.get("/documents", headers=headers)
    existing_documents = response.json["data"]
    for ed in existing_documents:
        response = client.delete(f'/documents/{ed["id"]}', headers=headers)
        assert response.status_code == 204

    # Trying to delete an non existing document
    response = client.delete(
        f'/documents/{existing_documents[0]["id"]}', headers=headers
    )
    assert response.status_code == 404
    assert not response.json["meta"]["success"]


def test_document_models(client):
    """Tests for document models management."""

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

    # Saving the user data
    user = response.json["data"]

    # Creating some test document categories
    test_document_categories = []
    for document_category_data in DOCUMENT_CATEGORIES_DATA:
        response = client.post(
            "/document-categories", headers=headers, json=document_category_data
        )
        assert response.status_code == 200
        assert response.json["meta"]["success"]
        # Saving created document category
        test_document_categories.append(response.json["data"])

    # Creating a new document
    with open("tests/assets/file.txt", "rb") as file:
        response = client.post(
            "/documents",
            headers=headers,
            data={
                "file": (file, "file.txt"),
                "code": "TXT-DOC",
                "description": "Text document",
                "observations": "The document contains a text file",
                "expires_at": "2023-12-01",
                "alert_email": "alert@email.com",
                "alert": 1,
                "days_to_alert": 7,
                "document_category_id": test_document_categories[0]["id"],
            },
        )
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    # Saving the created document
    document = response.json["data"]

    # Document model routes

    # Creating a new document model
    response = client.post(
        "/document-models",
        headers=headers,
        json={
            "model_name": "User",
            "model_id": user["id"],
            "document_id": document["id"],
        },
    )
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    # Saving new document model
    document_model = response.json["data"]

    # Trying to recreate a document model with document and model already associated
    response = client.post(
        "/document-models",
        headers=headers,
        json={
            "model_name": "User",
            "model_id": user["id"],
            "document_id": document["id"],
        },
    )
    assert response.status_code == 400
    assert not response.json["meta"]["success"]

    # Querying a document model and checking if response contains document and model data
    response = client.get(f'/document-models/{document_model["id"]}', headers=headers)
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    queried_document_model = response.json["data"]
    # Checking if relationships are present
    assert queried_document_model["document"]["id"] == document["id"]
    assert queried_document_model["model"]["id"] == user["id"]

    # Here, we'll try to delete a document which has a document model associated to it
    # To check if it will fail
    response = client.delete(f'/documents/{document["id"]}', headers=headers)
    assert response.status_code == 400
    assert not response.json["meta"]["success"]

    # Deleting the created document model
    response = client.delete(
        f'/document-models/{document_model["id"]}', headers=headers
    )
    assert response.status_code == 204

    # In the end, we'll also remove the created document and uploaded files
    response = client.delete(f'/documents/{document["id"]}', headers=headers)
    assert response.status_code == 204


def test_document_sharing(client):
    """Tests for document sharing."""

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

    # Saving the user data
    user = response.json["data"]

    # Creating some test document categories
    test_document_categories = []
    for document_category_data in DOCUMENT_CATEGORIES_DATA:
        response = client.post(
            "/document-categories", headers=headers, json=document_category_data
        )
        assert response.status_code == 200
        assert response.json["meta"]["success"]
        # Saving created document category
        test_document_categories.append(response.json["data"])

    # Creating some test document
    test_documents = []
    for i in range(0, 5):
        with open("tests/assets/file.txt", "rb") as file:
            response = client.post(
                "/documents",
                headers=headers,
                data={
                    "file": (file, f"file{i}.txt"),
                    "code": f"TXT-DOC-{i}",
                    "description": "Text document",
                    "observations": "The document contains a text file",
                    "expires_at": "2023-12-01",
                    "alert_email": "alert@email.com",
                    "alert": 1,
                    "days_to_alert": 7,
                    "document_category_id": test_document_categories[0]["id"],
                },
            )
        assert response.status_code == 200
        assert response.json["meta"]["success"]
        # Saving the created document
        test_documents.append(response.json["data"])

    # Creating another user to share documents with
    response = client.post("/users", headers=headers, json=SHARE_USER_DATA)
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    shared_user = response.json["data"]

    # Logging in with the shared user
    response = client.post("/auth/login", json=SHARE_USER_DATA)

    # Creating headers to set user authorization token
    share_headers = {"Authorization": f"Bearer {response.json['data']['token']}"}

    # Document sharing routes

    # Creating a new document sharing
    response = client.post(
        f'/documents/{test_documents[0]["id"]}/share',
        headers=headers,
        json={
            "shared_user_id": shared_user["id"],
        },
    )
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    # Saving new document sharing
    document_sharing = response.json["data"]

    # Trying to reshare a document with same user
    response = client.post(
        f'/documents/{test_documents[0]["id"]}/share',
        headers=headers,
        json={
            "shared_user_id": shared_user["id"],
        },
    )
    assert response.status_code == 400
    assert not response.json["meta"]["success"]

    # Trying to share a document with the document owner
    response = client.post(
        f'/documents/{test_documents[0]["id"]}/share',
        headers=headers,
        json={
            "shared_user_id": user["id"],
        },
    )
    assert response.status_code == 400
    assert not response.json["meta"]["success"]

    # Listing the documents shared with the other user
    response = client.get("/documents/shared", headers=share_headers)
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    # Saving the query result
    shared_documents = response.json["data"]
    # There should be one shared document and it must be the first created document
    assert len(shared_documents) == 1
    assert shared_documents[0]["id"] == test_documents[0]["id"]

    # Trying to share a document which does not belong to the user
    response = client.post(
        f'/documents/{test_documents[0]["id"]}/share',
        headers=share_headers,
        json={
            "shared_user_id": user["id"],
        },
    )
    assert response.status_code == 400
    assert not response.json["meta"]["success"]

    # Trying to stop sharing a document not shared by the user
    response = client.delete(
        f'/document-sharings/{document_sharing["id"]}', headers=share_headers
    )
    assert response.status_code == 400
    assert not response.json["meta"]["success"]

    # The listing of the owned documents by the main user must return the number of created documents
    # This is because all the documents were created by this user
    response = client.get("/documents/my", headers=headers)
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    assert response.json["meta"]["count"] == len(test_documents)
    # Since no document was created by the "shared user", its own documnts listing must be empty
    response = client.get("/documents/my", headers=share_headers)
    assert response.status_code == 200
    assert response.json["meta"]["success"]
    assert response.json["meta"]["count"] == 0

    # Now, we'll remove all the document sharings (unshare the documents) to remove associated documents
    # First we list the shared documents
    response = client.get("/document-sharings", headers=headers)
    document_sharings = response.json["data"]
    # Then, we'll unshare each one of them
    for ds in document_sharings:
        response = client.delete(f'/document-sharings/{ds["id"]}', headers=headers)
        assert response.status_code == 204

    # We'll also remove all the created documents (to remove uploaded files)
    for ed in test_documents:
        response = client.delete(f'/documents/{ed["id"]}', headers=headers)
        assert response.status_code == 204
