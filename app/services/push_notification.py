"""Third-party services to handle sending push notifications."""

import os
from typing import Optional, Dict, List, Any

from firebase_admin import messaging, credentials
import firebase_admin

from config import BASE_DIR

if os.environ.get("PUSH_NOTIFICATION_DRIVER") == "fcm":
    # Getting Firebase credentials
    creds = credentials.Certificate(
        BASE_DIR + os.sep + os.environ.get("FCM_CREDS_JSON_FILE")
    )

    # Initializing the Firebase app
    default_app = firebase_admin.initialize_app(creds)

    def send_message(
        token: str, title: str, body: str, data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Sends a push notification to a single device using a token.

        Args:
            token (str): The device token.
            title (str): Title of the notification.
            body (str): Body text of the notification.
            data (Optional[Dict[str, Any]]): Additional data payload.

        Returns:
            str: The server response from the notification.
        """
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data,
            token=token,
        )
        response = messaging.send(message)
        print("Message sent:", response)
        return response

    def send_multicast_message(
        tokens: List[str], title: str, body: str, data: Optional[Dict[str, Any]] = None
    ) -> Optional[messaging.BatchResponse]:
        """
        Sends a push notification to multiple devices using a list of tokens.

        Args:
            tokens (List[str]): A list of device tokens.
            title (str): Title of the notification.
            body (str): Body text of the notification.
            data (Optional[Dict[str, Any]]): Additional data payload.

        Returns:
            Optional[messaging.BatchResponse]: The server response if tokens are valid; otherwise, None.
        """
        try:
            assert isinstance(tokens, list)
        except AssertionError:
            print("Error: 'tokens' must be a list of strings.")
            return None

        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data,
            tokens=tokens,
        )
        response = messaging.send_multicast(message)
        print("Multicast message sent:", response)
        return response

else:

    def send_message(
        token: str, title: str, body: str, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Placeholder for sending a single notification if no driver is provided.

        Args:
            token (str): The device token.
            title (str): Title of the notification.
            body (str): Body text of the notification.
            data (Optional[Dict[str, Any]]): Additional data payload.
        """
        print("No driver provided for push notifications.")

    def send_multicast_message(
        tokens: List[str], title: str, body: str, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Placeholder for sending multicast notifications if no driver is provided.

        Args:
            tokens (List[str]): A list of device tokens.
            title (str): Title of the notification.
            body (str): Body text of the notification.
            data (Optional[Dict[str, Any]]): Additional data payload.
        """
        print("No driver provided for push notifications.")
