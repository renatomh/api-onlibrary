# -*- coding: utf-8 -*-

# Module to get the environment variables
import os

# Libraries for image processing
from PIL import Image

# Libraries for ffmpeg execution
import subprocess

# Libraries for PDF processing
# Check lincesing: https://github.com/pymupdf/PyMuPDF
# TL;DR: https://tldrlegal.com/license/gnu-affero-general-public-license-v3-(agpl-3.0)
import fitz

# Config variables
from config import ALLOWED_IMAGE_EXTENSIONS, ALLOWED_VIDEO_EXTENSIONS


# Function to generate a image thumbnail
def get_image_thumbnail(file, THUMB_SIZE=(512, 512)):
    # Getting the file extension and checking if it is allowed
    filename, file_extension = os.path.splitext(file)
    if file_extension not in Image.EXTENSION.keys():
        # If not allowed, we'll inform about the error
        print(
            "Invalid image format, must be one of the following",
            list(Image.EXTENSION.keys()),
        )
        # However, sometimes the list of extensions is not updated
        # Hence, we'll keep trying to create the image thumbnail

    # Trying to create the image thumbnail
    try:
        # Loading the image from the file
        image = Image.open(file)

        # Creating the image thumbnail according to the size (width, height)
        image.thumbnail(THUMB_SIZE)

        # JPEG cannot be written with alpha channel
        if image.mode in ("RGBA", "P"):
            # We'll also convert the image to RGB instead of RGBA
            image = image.convert("RGB")

        # Defining the thumbnail file name
        # We'll use JPEG since it has a better compression rate
        # Thumbnails usually don't need lossless compressions
        thumb_file = f"{filename}-thumb.jpg"

        # Saving the newly created thumbnail (as JPEG)
        # It'll be saved on the same folder as the original file
        image.save(thumb_file, "JPEG")

        # And returning the file path
        return thumb_file

    # If something goes wrong, we inform and return an empty object
    except Exception as e:
        print("Error while trying to create the image thumbnail", e)
        return None


# Function to generate a video thumbnail
def get_video_thumbnail(file, timestamp="00:00:00.000", THUMB_SIZE=None):
    # Getting the file name and extension
    filename, file_extension = os.path.splitext(file)

    # Trying to create the video thumbnail
    try:
        # Defining the thumbnail file name
        # We'll use JPEG since it has a better compression rate
        # Thumbnails usually don't need lossless compressions
        thumb_file = f"{filename}-thumb.jpg"

        # Getting the path for the FFmpeg executable
        # The FFmpeg must be installed on the machine
        ffmpeg = os.environ.get("FFMPEG_PATH")

        # Defining the args to call the FFmpeg execution
        args = [
            ffmpeg,  # Defining the executable file location
            "-y",  # Overwritting file if it already exists
            "-i",  # Starting the procedure
            file,  # Input video file
            "-ss",
            timestamp,  # Specific time/frame selected
            "-vframes",
            "1",  # Getting one frame (image)
        ]
        # If a specific size was provided for the thumbnail
        # Should be passed as a tuple (width, height)
        if THUMB_SIZE is not None:
            # We append to the FFmpeng options
            args.extend(["-s", f"{THUMB_SIZE[0]}x{THUMB_SIZE[1]}"])
        # Finally, we define the output image file for the args
        args.append(thumb_file)

        # Creating the video thumbnail
        subprocess.call(
            # Defiing the argments for the call
            args,
            # We also add a timeout, for performance purposes
            # If it takes too long, give up creating the thumbnail
            timeout=5,
        )

        # And returning the file path
        return thumb_file

    # If something goes wrong, we inform and return an empty object
    except Exception as e:
        print("Error while trying to create the video thumbnail", e)
        return None


# Function to generate a PDF file thumbnail
def get_pdf_thumbnail(file, page_no=0):
    # Getting the file extension and checking if it is allowed
    filename, file_extension = os.path.splitext(file)
    if file_extension.lower() != ".pdf":
        # If not allowed, we'll inform about the error
        print("Invalid PDF file format")
        # However, we'll keep trying to create the image thumbnail

    # Trying to create the PDF file thumbnail
    try:
        # Opening the PDF file
        doc = fitz.open(file)
        # Getting the PDF page to generate image
        page = doc.load_page(page_no)
        # Obtaining the page pixel map
        # That is, converting it to an image
        pix = page.get_pixmap()

        # Defining the thumbnail file name
        # We'll use JPEG since it has a better compression rate
        # Thumbnails usually don't need lossless compressions
        thumb_file = f"{filename}-thumb.jpg"

        # Saving the obtained image to the defined file
        pix.save(thumb_file)

        # And returning the file path
        return thumb_file

    # If something goes wrong, we inform and return an empty object
    except Exception as e:
        print("Error while trying to create the PDF thumbnail", e)
        return None


# Function to generate a generic file thumbnail
def get_file_thumbnail(file):
    # The first thing we'll do is get the file extension
    filename, file_extension = os.path.splitext(file)

    # If the file extension is within the list of allowed image extensions
    if file_extension in [f".{e}" for e in ALLOWED_IMAGE_EXTENSIONS]:
        # We'll try to generate the image thumbnail
        thumb_file = get_image_thumbnail(file)
        # And return the result
        return thumb_file

    # If the file extension is within the list of allowed video extensions
    if file_extension in [f".{e}" for e in ALLOWED_VIDEO_EXTENSIONS]:
        # We'll try to generate the video thumbnail
        thumb_file = get_video_thumbnail(file)
        # And return the result
        return thumb_file

    # If it is a PDF file
    if file_extension.lower() == ".pdf":
        # We'll try to generate the PDF file thumbnail
        thumb_file = get_pdf_thumbnail(file)
        # And return the result
        return thumb_file

    # For now, no other file formats can be used to generate thumbnails
    print("Thumbnail generation not available for file extension", file_extension)
    return None
