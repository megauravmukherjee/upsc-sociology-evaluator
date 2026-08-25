import os
import time
import tempfile
import io
from pypdf import PdfWriter
from google import genai
from google.genai import types

def test_gemini_file_upload():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not found in env.")
        return
        
    client = genai.Client(api_key=api_key)
    
    # Create sample PDF
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    pdf_bytes = buf.getvalue()
    
    temp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    temp_pdf.write(pdf_bytes)
    temp_pdf.close()
    
    print(f"Uploading file {temp_pdf.name} of size {len(pdf_bytes)} bytes...")
    try:
        uploaded_file = client.files.upload(
            file=temp_pdf.name,
            config=types.UploadFileConfig(mime_type="application/pdf")
        )
        print("Upload call returned! File object:", uploaded_file)
        print("File name:", uploaded_file.name)
        print("File state:", uploaded_file.state.name if hasattr(uploaded_file, 'state') else "No state attr")
    except Exception as e:
        print("Error uploading file:", e)
    finally:
        if os.path.exists(temp_pdf.name):
            os.remove(temp_pdf.name)

if __name__ == "__main__":
    test_gemini_file_upload()
