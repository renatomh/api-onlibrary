# -*- coding: utf-8 -*-

# Module to get the environment variables
import os

# Module to connect to SMTP server (Simple Mail Transfer Protocol)
import smtplib

# Module to allow files attachment
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid

# Module for AWS
import boto3
from botocore.exceptions import ClientError

# Modules to connect to IMAP server (Internet Message Access Protocol)
# And read email messages
import imaplib
import email
import re
from email.header import decode_header
from bs4 import BeautifulSoup

# Config variables
from config import OUTPUT_FOLDER

# Raw SMTP
if os.environ.get("MAIL_DRIVER") == "smtp":

    def send_mail(recipients, subject, body_html, attachment_paths=None, sender=None):
        # Defining the sender
        if sender is not None:
            _from = sender + f" <{os.environ.get('MAIL_USER')}>"
        else:
            _from = os.environ.get("MAIL_USER") + f" <{os.environ.get('MAIL_USER')}>"

        # Creating the e-mail content
        message = MIMEMultipart()
        message["From"] = _from
        message["Subject"] = subject
        # We should add the message ID, since some hosts require it
        message["Message-ID"] = make_msgid()

        # Defining the recipients
        # If a list was provided
        if type(recipients) == list:
            message["To"] = ", ".join(recipients)
        # If a single recipient was provided
        elif type(recipients) == str:
            message["To"] = recipients
        # If an unsupported data type was provided
        else:
            error_msg = "Unsupported data type provided for 'recipients'"
            print(error_msg)
            raise Exception(error_msg)

        # Attaching the mail body
        message.attach(MIMEText(body_html, "html"))

        # Inserting attachments (if present)
        if attachment_paths is not None:
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

        # Converting to string
        text = message.as_string()

        # Connecting to server and sending mail
        try:
            server = smtplib.SMTP_SSL(
                os.environ.get("SMTP_HOST"), os.environ.get("SMTP_PORT")
            )
            server.login(os.environ.get("MAIL_USER"), os.environ.get("MAIL_PASS"))
            server.sendmail(os.environ.get("MAIL_USER"), recipients, text)
            server.close()
        # If an exception is thrown
        except Exception as e:
            print("Error while trying to connect to email server.", e)


# Amazon AWS SES
elif os.environ.get("MAIL_DRIVER") == "ses":

    def send_mail(recipients, subject, body_html, attachment_paths=None, sender=None):
        # Reference: https://docs.aws.amazon.com/pt_br/ses/latest/DeveloperGuide/send-email-raw.html
        # Defining the sender
        if sender is not None:
            _from = sender + f" <{os.environ.get('MAIL_USER')}>"
        else:
            _from = os.environ.get("MAIL_USER") + f" <{os.environ.get('MAIL_USER')}>"

        # Creating the e-mail content
        message = MIMEMultipart()
        message["From"] = _from
        message["Subject"] = subject

        # Defining the recipients
        # If a list was provided
        if type(recipients) == list:
            message["To"] = ", ".join(recipients)
        # If a single recipient was provided
        elif type(recipients) == str:
            message["To"] = recipients
        # If an unsupported data type was provided
        else:
            error_msg = "Unsupported data type provided for 'recipients'"
            print(error_msg)
            raise Exception(error_msg)

        # Attaching the mail body
        message.attach(MIMEText(body_html, "html"))

        # Inserting attachments (if present)
        if attachment_paths is not None:
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

        # Converting to string
        text = message.as_string()

        # Create a new SES resource and specify a region.
        client = boto3.client(
            "ses",
            region_name=os.environ.get("AWS_REGION"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        )

        # Connecting to server and sending mail
        try:
            response = client.send_raw_email(
                Source=_from,
                Destinations=recipients,
                RawMessage={"Data": text},
            )
        # Display an error if something goes wrong.
        except ClientError as e:
            print(e.response["Error"]["Message"])
        else:
            print("Email sent! Message ID:"),
            print(response["MessageId"])


# Used for testing
elif os.environ.get("MAIL_DRIVER") == "test":

    def send_mail(recipients, subject, body_html, attachment_paths=None, sender=None):
        # Here, we'll just print out the data, so tests won't try to connect to mail host
        # Hence, tests will execute faster
        print(recipients, subject, body_html, attachment_paths, sender)
        return


# Function to extract text from HTMl
def extract_text_from_html(html):
    # Create a BeautifulSoup object to parse the HTML
    soup = BeautifulSoup(html, "html.parser")

    # Remove all script and style tags
    for script in soup(["script", "style"]):
        script.extract()

    # Get the text content from the HTML
    text = soup.get_text()

    # Remove extra whitespaces and newlines
    text = re.sub(r"\s+", " ", text).strip()

    # Returning the resulting text
    return text


# Function to read email messages
def read_email(
    no_messages=1,
    mailbox="INBOX",
    imap_host=os.environ.get("IMAP_HOST"),
    username=os.environ.get("MAIL_USER"),
    password=os.environ.get("MAIL_PASS"),
    filter_from="",
    filter_subject="",
    filter_body="",
    filter_seen_unseen="",
    filter_date="",
):
    # Initializing the list of email messages
    email_messages = []

    # Logging in to mail server with account credentials
    try:
        mail = imaplib.IMAP4_SSL(imap_host)
        mail.login(username, password)
    except Exception as e:
        print("Error while logging to mail server:", e)
        return email_messages

    # Building the filter query
    filter_query = "ALL"
    # It can be an email address, domain, part of it, e.g.: 'postmaster', '@gmail.com'
    filter_query += f' FROM "{filter_from}"' if len(filter_from) > 0 else ""
    filter_query += f' SUBJECT "{filter_subject}"' if len(filter_subject) > 0 else ""
    filter_query += f' BODY "{filter_body}"' if len(filter_body) > 0 else ""
    # '', 'SEEN' or 'UNSEEN'
    filter_query += f" {filter_seen_unseen}" if len(filter_seen_unseen) > 0 else ""
    # Sent at, e.g. '19-Feb-2015' (datetime.today().strftime("%d-%b-%Y"))
    filter_query += f" (ON {filter_date})" if len(filter_date) > 0 else ""

    # We can get a list of mailboxes with mail.list()
    # We can set the message to be marked as unread
    # status, messages = mail.select(mailbox, readonly=True)
    # Or set the message to be marked as read
    status, messages = mail.select(mailbox)

    # Searching emails
    try:
        status, data = mail.search(None, filter_query)
    except Exception as e:
        print("Error while searching mail:", e)
        mail.logout()
        return email_messages
    id_list = data[0].decode().split()
    id_list = list(map(int, id_list))

    # Sorting from most recent to older one
    id_list = sorted(id_list, reverse=True)
    id_list = id_list[0:no_messages]

    # For each message ID retrieved
    for message_id in id_list:
        email_messages.append(read_email_message(mail, message_id))

    # In the end, we logout
    mail.logout()

    # And return the list of email messages
    return email_messages


# Function to read an email message and download ataached files
def read_email_message(
    mail,
    message_id,
    attachments_folder=OUTPUT_FOLDER,
):
    # Dict to store read message data
    email_message = {
        "subject": None,
        "from": None,
        "to": None,
        "date": None,
        "body": None,
        "html": None,
        "attachments": None,
    }

    # Getting message by ID
    res, msg = mail.fetch(str(message_id), "(RFC822)")

    # If something goes wrong
    if res != "OK":
        print("Error while reading email:", res)
        return email_message

    # For each obtained result
    for response in msg:
        # Checking if is a tuple
        if isinstance(response, tuple):
            # Parsing email from bytes o message object
            msg = email.message_from_bytes(response[1])

            # Decoding email data and updating message dict
            # Subject
            try:
                Subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(Subject, bytes):
                    email_message["subject"] = Subject.decode(encoding)
            except Exception as e:
                print("Error while reading subject:", e)
            # Sender
            try:
                From, encoding = decode_header(msg.get("From"))[0]
                if isinstance(From, bytes):
                    email_message["from"] = From.decode(encoding)
                else:
                    email_message["from"] = From
            except Exception as e:
                print("Error while reading sender:", e)
            # Receiver
            try:
                To, encoding = decode_header(msg.get("To"))[0]
                if isinstance(To, bytes):
                    email_message["to"] = To.decode(encoding)
                else:
                    email_message["to"] = To
            except Exception as e:
                print("Error while reading receiver:", e)
            # Date
            try:
                Date, encoding = decode_header(msg.get("Date"))[0]
                if isinstance(Date, bytes):
                    email_message["date"] = Date.decode(encoding)
                else:
                    email_message["date"] = Date
            except Exception as e:
                print("Error while reading date:", e)

            # Checking for multipart message
            if msg.is_multipart():
                # Iterating parts
                for part in msg.walk():
                    # Getting part content type
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    content_encoding = part.get_content_charset()
                    # print(content_type, content_disposition, content_encoding)

                    # Getting email body
                    if content_type == "text/plain":
                        email_message["body"] = part.get_payload(decode=True).decode(
                            content_encoding
                        )
                    elif content_type == "text/html":
                        email_message["html"] = part.get_payload(decode=True).decode(
                            content_encoding
                        )
                    elif "attachment" in content_disposition:
                        # Downloading attachments
                        try:
                            file, encoding = decode_header(part.get_filename())[0]
                            if isinstance(file, bytes):
                                filename = file.decode(encoding)
                            else:
                                filename = file
                            if file:
                                # Creating file path for attachment
                                filepath = os.path.join(attachments_folder, filename)
                                # Saving file
                                open(filepath, "wb").write(
                                    part.get_payload(decode=True)
                                )
                                email_message["attachments"] = filepath
                        except Exception as e:
                            print(
                                "Error while getting attachment data:",
                                Subject,
                                filename,
                                e,
                            )

            # Other types of messages
            else:
                # Getting message content type
                content_type = msg.get_content_type()
                content_encoding = msg.get_content_charset()
                # print (content_type, content_encoding)
                # Getting email body
                body = msg.get_payload(decode=True).decode(content_encoding)
                # Updating message dict
                email_message["body"] = body

                # For HTML messages
                if content_type == "text/html":
                    email_message["html"] = part.get_payload(decode=True).decode(
                        content_encoding
                    )

    # In the end, if we have an empty body field, we'll clean the HTML to
    # get the message body
    if not email_message["body"]:
        email_message["body"] = extract_text_from_html(email_message["html"])

    # Finally, we return the dict with email contents
    return email_message
