# -*- coding: utf-8 -*-

# Import flask dependencies
from flask_babel import _

# Import Socket.IO dependencies
from app import socketio

# Import services
from app.services.push_notification import send_message

# Import module models
from app.modules.users.models import *
from app.modules.notification.models import *

# Function to notify a user via Socket.IO (for front-end application)
def notify_user_via_socketio(user_id, title, content, session, event='notification'):
    # Getting the user object
    user = session.query(User).get(user_id)

    # If the user has a Socket.IO session ID set
    if user.socketio_sid:
        # Emitting the notification to the use session ID
        socketio.emit(event, {'title': title, 'content': content}, to=user.socketio_sid)

    # In the end, we just return the function
    return

# Function to notify a user via push notifications (for mobile application)
def notify_user_via_push_notification(user_id, title, content, session):
    # Getting the user object
    user = session.query(User).get(user_id)

    # If the user has a FCM toke set
    if user.fcm_token:
        # Sending the notification for the token
        try: send_message(user.fcm_token, title, content)
        # If an error occurs
        except Exception as e: print('Error while sending push notification', str(e))

    # In the end, we just return the function
    return

# Function to generate a user notification and notify it on specified channels
def notify_user(user_id, title, content, session, web_action=None, mobile_action=None,
    send_socketio_notification=True, send_push_notification=True):
    # Checking if user exists
    user = User.query.get(user_id)
    if user is None:
        print('No user found')
        return

    # Creating new item
    item = Notification(
        title=title,
        description=content,
        user_id=user_id,
        web_action=web_action,
        mobile_action=mobile_action,
        )
    session.add(item)
    session.flush()
    session.commit()

    # Notifying user on front-end
    if send_socketio_notification:
        notify_user_via_socketio(item.user_id, item.title, item.description, session)
    # Notifying user on mobile application
    if send_push_notification:
        notify_user_via_push_notification(item.user_id, item.title, item.description, session)
