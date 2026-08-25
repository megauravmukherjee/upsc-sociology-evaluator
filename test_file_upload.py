import tempfile
import os
import io
from pypdf import PdfWriter

def create_sample_pdf():
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()

if __name__ == "__main__":
    pdf_bytes = create_sample_pdf()
    print(f"Created sample PDF of {len(pdf_bytes)} bytes.")
