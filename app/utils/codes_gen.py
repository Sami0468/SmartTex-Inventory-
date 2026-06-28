"""
QR code & barcode generation for fabric rolls.
"""
import os
import qrcode
from barcode import Code128
from barcode.writer import ImageWriter
from flask import current_app


def generate_qr_code(fabric_code, data_text):
    """Generate a QR code PNG for a fabric and return its relative static path."""
    folder = current_app.config["QRCODE_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    filename = f"{fabric_code}.png"
    filepath = os.path.join(folder, filename)

    img = qrcode.make(data_text)
    img.save(filepath)

    return f"uploads/qrcodes/{filename}"


def generate_barcode(fabric_code):
    """Generate a Code128 barcode PNG for a fabric and return its relative static path."""
    folder = current_app.config["BARCODE_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    filename_noext = fabric_code
    filepath_noext = os.path.join(folder, filename_noext)

    code = Code128(fabric_code, writer=ImageWriter())
    saved_path = code.save(filepath_noext)  # returns full path with extension

    return f"uploads/barcodes/{os.path.basename(saved_path)}"
