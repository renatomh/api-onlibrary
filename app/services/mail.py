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

# Module for AWS
import boto3
from botocore.exceptions import ClientError

# Raw SMTP
if os.environ.get('MAIL_DRIVER') == 'smtp':
    def send_mail(recipients, subject, body_html, attachment_paths=None, sender=None):
        # Defining the sender
        if (sender is not None):
            _from = sender + f" <{os.environ.get('MAIL_USER')}>"
        else:
            _from = os.environ.get('MAIL_USER') + \
                f" <{os.environ.get('MAIL_USER')}>"

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
                    part = MIMEBase('application', 'octet-stream')
                    part.add_header('Content-Disposition', 'attachment',
                                    filename=os.path.basename(attachment_path))
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    message.attach(part)

        # Converting to string
        text = message.as_string()

        # Connecting to server and sending mail
        try:
            server = smtplib.SMTP_SSL(os.environ.get(
                'SMTP_HOST'), os.environ.get('SMTP_PORT'))
            server.login(os.environ.get('MAIL_USER'),
                         os.environ.get('MAIL_PASS'))
            server.sendmail(os.environ.get('MAIL_USER'), recipients, text)
            server.close()
        # If an exception is thrown
        except Exception as e:
            print('Error while trying to connect to email server.', e)

# Amazon AWS SES
elif os.environ.get('MAIL_DRIVER') == 'ses':
    def send_mail(recipients, subject, body_html, attachment_paths=None, sender=None):
        # Reference: https://docs.aws.amazon.com/pt_br/ses/latest/DeveloperGuide/send-email-raw.html
        # Defining the sender
        if (sender is not None):
            _from = sender + f" <{os.environ.get('MAIL_USER')}>"
        else:
            _from = os.environ.get('MAIL_USER') + \
                f" <{os.environ.get('MAIL_USER')}>"

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
                    part = MIMEBase('application', 'octet-stream')
                    part.add_header('Content-Disposition', 'attachment',
                                    filename=os.path.basename(attachment_path))
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    message.attach(part)

        # Converting to string
        text = message.as_string()

        # Create a new SES resource and specify a region.
        client = boto3.client(
            'ses',
            region_name=os.environ.get('AWS_REGION'),
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
        )

        # Connecting to server and sending mail
        try:
            response = client.send_raw_email(
                Source=_from,
                Destinations=recipients,
                RawMessage={'Data': text},
            )
        # Display an error if something goes wrong.	
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            print("Email sent! Message ID:"),
            print(response['MessageId'])
