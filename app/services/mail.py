"""Third-party services to handle sending and reading email messages."""

import os
import re
import smtplib
import imaplib
import email
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid
from email.header import decode_header
from typing import Optional, Union, List, Dict, Any

import boto3
from botocore.exceptions import ClientError
from bs4 import BeautifulSoup

from config import OUTPUT_FOLDER

if os.environ.get("MAIL_DRIVER") == "smtp":

    def send_mail(
        recipients: Union[str, List[str]],
        subject: str,
        body_html: str,
        attachment_paths: Optional[List[str]] = None,
        sender: Optional[str] = None,
    ) -> None:
        """
        Sends an email with optional attachments using SMTP.

        Args:
            recipients (Union[str, List[str]]): The email recipient(s).
            subject (str): The subject of the email.
            body_html (str): The HTML body of the email.
            attachment_paths (Optional[List[str]]): Paths to files to attach to the email.
            sender (Optional[str]): The sender's name.

        Raises:
            Exception: If an unsupported data type is provided for 'recipients'.
        """
        _from = (
            f"{sender} <{os.environ.get('MAIL_USER')}>"
            if sender
            else f"{os.environ.get('MAIL_USER')} <{os.environ.get('MAIL_USER')}>"
        )

        # Create the email content
        message = MIMEMultipart()
        message["From"] = _from
        message["Subject"] = subject
        message["Message-ID"] = make_msgid()

        # Set recipients
        if isinstance(recipients, list):
            message["To"] = ", ".join(recipients)
        elif isinstance(recipients, str):
            message["To"] = recipients
        else:
            raise Exception("Unsupported data type provided for 'recipients'")

        message.attach(MIMEText(body_html, "html"))

        # Attach files
        if attachment_paths:
            for attachment_path in attachment_paths:
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=os.path.basename(attachment_path),
                    )
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    message.attach(part)

        try:
            server = smtplib.SMTP_SSL(
                os.environ.get("SMTP_HOST"), int(os.environ.get("SMTP_PORT"))
            )
            server.login(os.environ.get("MAIL_USER"), os.environ.get("MAIL_PASS"))
            server.sendmail(
                os.environ.get("MAIL_USER"), recipients, message.as_string()
            )
            server.close()
        except Exception as e:
            print("Error while trying to connect to email server.", e)

elif os.environ.get("MAIL_DRIVER") == "ses":

    def send_mail(
        recipients: Union[str, List[str]],
        subject: str,
        body_html: str,
        attachment_paths: Optional[List[str]] = None,
        sender: Optional[str] = None,
    ) -> None:
        """
        Sends an email with optional attachments using AWS SES.

        Args:
            recipients (Union[str, List[str]]): The email recipient(s).
            subject (str): The subject of the email.
            body_html (str): The HTML body of the email.
            attachment_paths (Optional[List[str]]): Paths to files to attach to the email.
            sender (Optional[str]): The sender's name.

        Raises:
            Exception: If an unsupported data type is provided for 'recipients'.
        """
        _from = (
            f"{sender} <{os.environ.get('MAIL_USER')}>"
            if sender
            else f"{os.environ.get('MAIL_USER')} <{os.environ.get('MAIL_USER')}>"
        )

        message = MIMEMultipart()
        message["From"] = _from
        message["Subject"] = subject

        if isinstance(recipients, list):
            message["To"] = ", ".join(recipients)
        elif isinstance(recipients, str):
            message["To"] = recipients
        else:
            raise Exception("Unsupported data type provided for 'recipients'")

        message.attach(MIMEText(body_html, "html"))

        if attachment_paths:
            for attachment_path in attachment_paths:
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=os.path.basename(attachment_path),
                    )
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    message.attach(part)

        client = boto3.client(
            "ses",
            region_name=os.environ.get("AWS_REGION"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        )

        try:
            response = client.send_raw_email(
                Source=_from,
                Destinations=(
                    [recipients] if isinstance(recipients, str) else recipients
                ),
                RawMessage={"Data": message.as_string()},
            )
            print("Email sent! Message ID:", response["MessageId"])
        except ClientError as e:
            print(e.response["Error"]["Message"])

elif os.environ.get("MAIL_DRIVER") == "test":

    def send_mail(
        recipients: Union[str, List[str]],
        subject: str,
        body_html: str,
        attachment_paths: Optional[List[str]] = None,
        sender: Optional[str] = None,
    ) -> None:
        """
        Simulates sending an email by printing the email contents.

        Args:
            recipients (Union[str, List[str]]): The email recipient(s).
            subject (str): The subject of the email.
            body_html (str): The HTML body of the email.
            attachment_paths (Optional[List[str]]): Paths to files to attach to the email.
            sender (Optional[str]): The sender's name.
        """
        print(recipients, subject, body_html, attachment_paths, sender)


def extract_text_from_html(html: str) -> str:
    """
    Extracts and cleans text from HTML content.

    Args:
        html (str): The HTML content.

    Returns:
        str: Cleaned text from HTML.
    """
    soup = BeautifulSoup(html, "html.parser")
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text()
    return re.sub(r"\s+", " ", text).strip()


def read_email(
    no_messages: int = 1,
    mailbox: str = "INBOX",
    imap_host: Optional[str] = os.environ.get("IMAP_HOST"),
    username: Optional[str] = os.environ.get("MAIL_USER"),
    password: Optional[str] = os.environ.get("MAIL_PASS"),
    filter_from: str = "",
    filter_subject: str = "",
    filter_body: str = "",
    filter_seen_unseen: str = "",
    filter_date: str = "",
) -> List[Dict[str, Any]]:
    """
    Reads and filters email messages from an IMAP mailbox.

    Args:
        no_messages (int): Number of messages to fetch.
        mailbox (str): Mailbox folder name.
        imap_host (Optional[str]): IMAP host.
        username (Optional[str]): Username for the mailbox.
        password (Optional[str]): Password for the mailbox.
        filter_from (str): Filter by sender.
        filter_subject (str): Filter by subject.
        filter_body (str): Filter by body content.
        filter_seen_unseen (str): Filter by read/unread status.
        filter_date (str): Filter by date.

    Returns:
        List[Dict[str, Any]]: List of email messages.
    """
    email_messages = []

    try:
        mail = imaplib.IMAP4_SSL(imap_host)
        mail.login(username, password)
    except Exception as e:
        print("Error while logging to mail server:", e)
        return email_messages

    filter_query = "ALL"
    filter_query += f' FROM "{filter_from}"' if filter_from else ""
    filter_query += f' SUBJECT "{filter_subject}"' if filter_subject else ""
    filter_query += f' BODY "{filter_body}"' if filter_body else ""
    filter_query += f" {filter_seen_unseen}" if filter_seen_unseen else ""
    filter_query += f" (ON {filter_date})" if filter_date else ""

    status, messages = mail.select(mailbox)

    try:
        status, data = mail.search(None, filter_query)
    except Exception as e:
        print("Error while searching mail:", e)
        mail.logout()
        return email_messages
    id_list = list(map(int, data[0].decode().split()))
    id_list = sorted(id_list, reverse=True)[:no_messages]

    for message_id in id_list:
        email_messages.append(read_email_message(mail, message_id))

    mail.logout()
    return email_messages


def read_email_message(
    mail: imaplib.IMAP4_SSL, message_id: int, attachments_folder: str = OUTPUT_FOLDER
) -> Dict[str, Any]:
    """
    Reads a single email message by ID and saves attachments.

    Args:
        mail (imaplib.IMAP4_SSL): The IMAP connection object.
        message_id (int): The ID of the email message.
        attachments_folder (str): Path to the folder to save attachments.

    Returns:
        Dict[str, Any]: Parsed email data.
    """
    status, msg_data = mail.fetch(str(message_id), "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])

    message_details = {
        "from": decode_header(msg["From"])[0][0],
        "subject": decode_header(msg["Subject"])[0][0],
        "date": msg["Date"],
        "body": "",
        "attachments": [],
    }

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in part.get(
                "Content-Disposition", ""
            ):
                message_details["body"] = part.get_payload(decode=True).decode()
            elif part.get("Content-Disposition") and "attachment" in part.get(
                "Content-Disposition"
            ):
                filename = part.get_filename()
                if filename:
                    filepath = os.path.join(attachments_folder, filename)
                    with open(filepath, "wb") as f:
                        f.write(part.get_payload(decode=True))
                    message_details["attachments"].append(filepath)
    else:
        message_details["body"] = msg.get_payload(decode=True).decode()
    return message_details
