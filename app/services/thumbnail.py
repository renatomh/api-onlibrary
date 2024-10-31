"""Services to handle thumbnails creation."""

import os
from PIL import Image
import subprocess
from typing import Optional, Tuple

# Libraries for PDF processing
import fitz

from config import ALLOWED_IMAGE_EXTENSIONS, ALLOWED_VIDEO_EXTENSIONS


def get_image_thumbnail(
    file: str, THUMB_SIZE: Tuple[int, int] = (512, 512)
) -> Optional[str]:
    """
    Generates a thumbnail for an image file.

    Args:
        file (str): The path to the image file.
        THUMB_SIZE (Tuple[int, int]): The desired size of the thumbnail (width, height).

    Returns:
        Optional[str]: The path to the created thumbnail, or None if an error occurred.
    """
    filename, file_extension = os.path.splitext(file)
    if file_extension not in Image.EXTENSION.keys():
        print(
            "Invalid image format, must be one of the following",
            list(Image.EXTENSION.keys()),
        )

    try:
        image = Image.open(file)
        image.thumbnail(THUMB_SIZE)

        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        thumb_file = f"{filename}-thumb.jpg"
        image.save(thumb_file, "JPEG")

        return thumb_file

    except Exception as e:
        print("Error while trying to create the image thumbnail", e)
        return None


def get_video_thumbnail(
    file: str,
    timestamp: str = "00:00:00.000",
    THUMB_SIZE: Optional[Tuple[int, int]] = None,
) -> Optional[str]:
    """
    Generates a thumbnail for a video file at a specified timestamp.

    Args:
        file (str): The path to the video file.
        timestamp (str): The timestamp to capture the thumbnail from (format: HH:MM:SS.sss).
        THUMB_SIZE (Optional[Tuple[int, int]]): The desired size of the thumbnail (width, height).

    Returns:
        Optional[str]: The path to the created thumbnail, or None if an error occurred.
    """
    filename, file_extension = os.path.splitext(file)

    try:
        thumb_file = f"{filename}-thumb.jpg"
        ffmpeg = os.environ.get("FFMPEG_PATH")

        args = [
            ffmpeg,
            "-y",
            "-i",
            file,
            "-ss",
            timestamp,
            "-vframes",
            "1",
        ]
        if THUMB_SIZE is not None:
            args.extend(["-s", f"{THUMB_SIZE[0]}x{THUMB_SIZE[1]}"])
        args.append(thumb_file)

        subprocess.call(args, timeout=5)

        return thumb_file

    except Exception as e:
        print("Error while trying to create the video thumbnail", e)
        return None


def get_pdf_thumbnail(file: str, page_no: int = 0) -> Optional[str]:
    """
    Generates a thumbnail for a specific page of a PDF file.

    Args:
        file (str): The path to the PDF file.
        page_no (int): The page number to generate the thumbnail from (0-based index).

    Returns:
        Optional[str]: The path to the created thumbnail, or None if an error occurred.
    """
    filename, file_extension = os.path.splitext(file)
    if file_extension.lower() != ".pdf":
        print("Invalid PDF file format")

    try:
        doc = fitz.open(file)
        page = doc.load_page(page_no)
        pix = page.get_pixmap()

        thumb_file = f"{filename}-thumb.jpg"
        pix.save(thumb_file)

        return thumb_file

    except Exception as e:
        print("Error while trying to create the PDF thumbnail", e)
        return None


def get_file_thumbnail(file: str) -> Optional[str]:
    """
    Generates a thumbnail for a file based on its extension.

    Args:
        file (str): The path to the file.

    Returns:
        Optional[str]: The path to the created thumbnail, or None if no thumbnail could be generated.
    """
    filename, file_extension = os.path.splitext(file)

    if file_extension in [f".{e}" for e in ALLOWED_IMAGE_EXTENSIONS]:
        return get_image_thumbnail(file)

    if file_extension in [f".{e}" for e in ALLOWED_VIDEO_EXTENSIONS]:
        return get_video_thumbnail(file)

    if file_extension.lower() == ".pdf":
        return get_pdf_thumbnail(file)

    print("Thumbnail generation not available for file extension", file_extension)
    return None
