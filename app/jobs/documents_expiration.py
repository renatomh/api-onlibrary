# -*- coding: utf-8 -*-
"""
Main function to notify users about expiring documents

Important:
* This script should be called on the app's root folder, since its 
    imports depend on it;
* The integration user credentials ("INTEGRATION_USER" and 
    "INTEGRATION_PASS") must be set on the .env file;

"""

# Import module models
from app.modules.document.models import Document

# Other imports
from datetime import datetime, timedelta
import sys, os, requests, json

# This job should be executed only when called directly,
# not when imported from other modules/packages
if __name__ == "__main__":
    # Getting current date
    # Checking is a specific date was provided (format example: 2022-12-31)
    try: current_date = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
    except: current_date = datetime.today().date()

    # Here, we're going to query the documents which expiration should be alerted
    # And which alert date hasn't passed yet
    alert_documents = Document.query.filter(
        Document.alert==1,
        Document.expires_at>=current_date,
    ).all()

    # Filtering out by the documents which should be alerted at the current date
    documents_to_notify = [doc for doc in alert_documents 
        if doc.expires_at==current_date+timedelta(days=doc.days_to_alert)]

    # Here, we'll make requests to the running locar server API, since we want
    # to avoid problems with translations, notification sending and rendering
    # It works like a microservice

    # Setting the server host (API URL)
    api_base_url = os.getenv('APP_API_URL')
    # Setting request headers
    headers = {
        # Defining the content type
        'Content-Type': 'application/json',
        # Here, we can set the desired language
        # For example, if users have preferred languages set
        'Accept-Language': 'pt, en;q=0.7, es;q=0.5',
    }

    # Logging in with the integration user
    res = requests.request(
        "POST", 
        f"{api_base_url}/auth/login", 
        headers=headers,
        # Defining data to be passed to login request
        data=json.dumps({
            "username": os.getenv('INTEGRATION_USER'),
            "password": os.getenv('INTEGRATION_PASS'),
        })
        )

    # If login is successful, we set the token to the headers
    if res.ok: headers['Authorization'] = f"Bearer {json.loads(res.text)['data']['token']}"
    # Otherwise, we return and end the function
    else:
        print("Error on login")
        sys.exit()

    # Now, for each document to be notified, we'll call the notification function
    for document in documents_to_notify:
        # Calling the API route
        res = requests.request("POST", f"{api_base_url}/documents/{document.id}/notify_expiration", headers=headers)
        # Showing the result of the requests
        print(res.status_code, res.text)
