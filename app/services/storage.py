"""Third-party services to handle files storage."""

import os
import mimetypes
from typing import Optional, Dict, Any

import boto3
from botocore.exceptions import ClientError

from config import UPLOAD_FOLDER

if os.environ.get("STORAGE_DRIVER") == "disk":

    def store_file(file: str, object_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Stores a file on the local disk.

        Args:
            file (str): The path of the file to be stored.
            object_name (Optional[str]): The name to save the file as; if None, uses the file's current name.

        Returns:
            Dict[str, Any]: A dictionary containing metadata about the stored file.
        """
        if object_name is None:
            object_name = os.path.basename(file)

        try:
            os.rename(file, os.path.join(UPLOAD_FOLDER, object_name))
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

    def remove_file(object_name: str) -> Dict[str, Any]:
        """
        Removes a file from local disk storage.

        Args:
            object_name (str): The name of the file to remove.

        Returns:
            Dict[str, Any]: A dictionary indicating success or failure of the operation.
        """
        try:
            os.remove(os.path.join(UPLOAD_FOLDER, object_name))
            return {"data": {}, "meta": {"success": True}}
        except Exception as e:
            print("Error while removing file:", e)
            return {
                "success": False,
                "errors": f"An error occurred while removing the file: {e}",
            }

elif os.environ.get("STORAGE_DRIVER") == "s3":

    def store_file(file: str, object_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Stores a file in an S3 bucket.

        Args:
            file (str): The path of the file to be stored.
            object_name (Optional[str]): The name to save the file as in S3; if None, uses the file's current name.

        Returns:
            Dict[str, Any]: A dictionary containing metadata about the stored file.
        """
        if object_name is None:
            object_name = os.path.basename(file)

        client = boto3.client(
            "s3",
            region_name=os.environ.get("AWS_REGION"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        )

        try:
            content_type = (
                mimetypes.guess_type(file)[0]
                if isinstance(mimetypes.guess_type(file), tuple)
                else None
            )

            client.upload_file(
                file,
                os.environ.get("AWS_BUCKET"),
                object_name,
                ExtraArgs={"ACL": "public-read", "ContentType": content_type},
            )
            os.remove(file)
            return {
                "data": {
                    "object_name": object_name,
                    "file_url": "https://"
                    + os.environ.get("AWS_BUCKET")
                    + ".s3."
                    + os.environ.get("AWS_REGION")
                    + ".amazonaws.com/"
                    + object_name,
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

    def remove_file(object_name: str) -> Dict[str, Any]:
        """
        Removes a file from an S3 bucket.

        Args:
            object_name (str): The name of the file to remove.

        Returns:
            Dict[str, Any]: A dictionary indicating success or failure of the operation.
        """
        client = boto3.client(
            "s3",
            region_name=os.environ.get("AWS_REGION"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        )

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
