# -*- coding: utf-8 -*-

# Import flask dependencies
from flask import render_template
from flask_babel import _

# Import services
from app.services.mail import send_mail

# Import module models
from app.modules.document.models import *

# Utilities functions
from app.modules.notification.utils import *

# Other imports
from datetime import datetime
from humanize import naturalsize

# Function to send a notification for an expiring document
def notify_document_expiration(document_id, session):
    # Getting the document object
    document = Document.query.get(document_id)

    # Preparing data for replacing in the template
    data = {
        # General data
        'code': document.code,
        'description': document.description,
        'observations': document.observations,
        'expires_at': document.expires_at,
        'days_to_expire': (document.expires_at - datetime.today().date()).days,
        # User data
        'user': document.user,
        # File
        'file_name': document.file_name,
        'file_content_type': document.file_content_type,
        'file_size': naturalsize(document.file_size),
        # Link/URL for the document file
        'link': document.full_file_url(),
    }
    
    # Replacing data in jinja2 template
    body_html = render_template('emails/document_expiration.html', **data)

    # If there is a email address registered for notification
    if document.alert_email is not None:
        # Trying to send the email
        try:
            # Sending notification mail
            send_mail(
                recipients=[document.alert_email],
                subject=_('Document Expiration') + f': "{document.file_name}"',
                body_html=body_html,
                sender='Postmaster | OnLibrary'
            )
        # If an error occurs
        except Exception as e:
            print ('An error occurred while trying to notify the users via email', e)
    
    # Otherwise, there will be no addresses to receive the email message
    else:
        print ('No email addresses registered for the notification')
    
    # We'll also create a notification for the docuemtn owner
    content = _('Your document is about to expire')
    content += "\n* " + _('Expires At') + f": {document.expires_at} ({data['days_to_expire']} " + _('days') + ");"
    content += "\n* " + _('Description') + f": {document.description};"
    content += "\n* " + _('File') + f": {data['file_name']} ({data['file_content_type']} {data['file_size']});"
    notify_user(
        user_id=document.user_id,
        title=_('Document Expiration') + f': "{document.file_name}"',
        content=content,
        session=session,
        web_action=data['link'],
    )
    
    # Flushing and committing the changes on the database session
    session.flush()
    session.commit()
