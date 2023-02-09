# -*- coding: utf-8 -*-

# Module to get the environment variables
import os

# Getting the required variables
from config import OUTPUT_FOLDER

# QR Code Library
import qrcode

# Function to generate QR code from provided data
def get_qr_code(input_data, filename='qrcode'):
    # Creating an instance of QR Code
    qr = qrcode.QRCode(
        version=1,      # Using smallest verstion (21x21)
        box_size=15,    # Setting QR code size
        border=2,       # Borders for the image
        # With this option, about 30% or fewer errors can be corrected
        error_correction=qrcode.constants.ERROR_CORRECT_H
    )

    # Adding specified data
    qr.add_data(input_data)
    # Creating QR Code and fitting to the box
    qr.make(fit=True)
    # Converting object into image
    img = qr.make_image(fill='black', back_color='white')
    
    # Defining the file path based on the file name
    filepath = OUTPUT_FOLDER + os.sep + filename + '.png'

    # Saving QR Code as an image
    img.save(filepath)

    # Returning the path for the newly created item
    return filepath
