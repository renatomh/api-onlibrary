# -*- coding: utf-8 -*-

# Module to get the environment variables
import os

# Module for AWS
import boto3
from botocore.exceptions import ClientError

# Getting the required variables
from config import UPLOAD_FOLDER

# Moduloe to obtain ContentType from files
import mimetypes

# Disk Storage
if os.environ.get("STORAGE_DRIVER") == "disk":

    def store_file(file, object_name=None):
        # If object_name was not specified, use file's current name
        if object_name is None:
            object_name = os.path.basename(file)

        # Moving file to new location
        try:
            os.rename(file, UPLOAD_FOLDER + os.sep + object_name)
            return {
                "data": {
                    "object_name": object_name,
                    "file_url": f'{os.environ.get("APP_API_URL")}/files/{object_name}',
                },
                "meta": {"success": True},
            }
        except Exception as e:
            print("Error while uploading file:", e)
            return {
                "success": False,
                "errors": f"An error occurred while uploading the file: {e}",
            }

    def remove_file(object_name):
        # Removing the selected file by object name
        try:
            os.remove(UPLOAD_FOLDER + os.sep + object_name)
            return {"data": {}, "meta": {"success": True}}
        except Exception as e:
            print("Error while removing file:", e)
            return {
                "success": False,
                "errors": f"An error occurred while removing the file: {e}",
            }


# Amazon AWS S3
elif os.environ.get("STORAGE_DRIVER") == "s3":

    def store_file(file, object_name=None):
        # Reference: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-uploading-files.html
        # If object_name was not specified, use file's current name
        if object_name is None:
            object_name = os.path.basename(file)

        # Create a new S3 resource and specify a region.
        client = boto3.client(
            "s3",
            region_name=os.environ.get("AWS_REGION"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        )

        # Uploading the file
        try:
            # Trying to get the file ContentType
            content_type = None
            if type(mimetypes.guess_type(file)) == tuple:
                content_type = mimetypes.guess_type(file)[0]

            client.upload_file(
                file,
                os.environ.get("AWS_BUCKET"),
                object_name,
                ExtraArgs={"ACL": "public-read", "ContentType": content_type},
            )
            # Removing the local file
            os.remove(file)
            return {
                "data": {
                    "object_name": object_name,
                    "file_url": f'https://{os.environ.get("AWS_BUCKET")}.s3.{os.environ.get("AWS_REGION")}.amazonaws.com/{object_name}',
                },
                "meta": {"success": True},
            }
        except ClientError as e:
            return {
                "data": {},
                "meta": {
                    "success": False,
                    "errors": f"An error occurred while uploading the file: {e}",
                },
            }

    def remove_file(object_name):
        # Create a new S3 resource and specify a region.
        client = boto3.client(
            "s3",
            region_name=os.environ.get("AWS_REGION"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        )

        # Removing the file
        try:
            client.delete_object(Bucket=os.environ.get("AWS_BUCKET"), Key=object_name)
            return {"data": {}, "meta": {"success": True}}
        except ClientError as e:
            return {
                "data": {},
                "meta": {
                    "success": False,
                    "errors": f"An error occurred while removing the file: {e}",
                },
            }
