"""
Main function to notify users about expiring documents.

Important:
* This script should be called on the app's root folder, since its imports depend on it;
* The integration user credentials ("INTEGRATION_USER" and "INTEGRATION_PASS") must be set on the .env file;
"""

import os
import sys
import requests
import json
from datetime import datetime, timedelta

from app.modules.document.models import Document

if __name__ == "__main__":
    # Getting date to check for expiration
    try:
        current_date = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
    except:
        current_date = datetime.today().date()

    # Query documents to be alerted which haven't expired yet
    alert_documents = Document.query.filter(
        Document.alert == 1,
        Document.expires_at >= current_date,
    ).all()

    # Filtering documents to be alerted at the specified date
    documents_to_notify = [
        doc
        for doc in alert_documents
        if doc.expires_at == current_date + timedelta(days=doc.days_to_alert)
    ]

    # Requests running local server API, to avoid problems with translations, notification sending and rendering, like
    # a microservice

    # Setting up the request
    api_base_url = os.getenv("APP_API_URL")
    headers = {
        "Content-Type": "application/json",
        # We can set the desired language if users have preferred languages set
        "Accept-Language": "pt, en;q=0.7, es;q=0.5",
    }

    # Login with the integration user
    res = requests.request(
        "POST",
        f"{api_base_url}/auth/login",
        headers=headers,
        # Defining data to be passed to login request
        data=json.dumps(
            {
                "username": os.getenv("INTEGRATION_USER"),
                "password": os.getenv("INTEGRATION_PASS"),
            }
        ),
    )
    if res.ok:
        headers["Authorization"] = f"Bearer {json.loads(res.text)['data']['token']}"
    else:
        print("Error on login")
        sys.exit()

    # For each document to be notified, call the notification function
    for document in documents_to_notify:
        res = requests.request(
            "POST",
            f"{api_base_url}/documents/{document.id}/notify_expiration",
            headers=headers,
        )
        print(res.status_code, res.text)
