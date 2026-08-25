import io
import os
import time
import tempfile
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from pypdf import PdfReader
from google import genai
from google.genai import types
import config

def get_client(api_key=None):
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("Gemini API key is required. Please set GEMINI_API_KEY environment variable or provide it in the UI.")
    return genai.Client(api_key=key)

def process_pdf_or_image(file_bytes, filename, api_key=None, progress_callback=None):
    """
    Processes uploaded file (PDF or Image) using Gemini Files API for ultra-fast PDF OCR.
    Bypasses slow CPU image extraction and handles large multi-page PDFs natively in Gemini cloud.
    """
    client = get_client(api_key)
    filename_lower = filename.lower()
    
    ocr_prompt = """
    You are an expert OCR and document analysis engine specialized in UPSC Civil Services Examination (CSE) answer papers.
    Transcribe all handwritten text, question numbers (Q1, Q2, etc.), side notes, and diagram descriptions from this document accurately.
    Organize the transcription page by page formatted as:
    --- [Page X] ---
    [Transcribed Text]
    """

    if filename_lower.endswith(".pdf"):
        # 1. High-speed Gemini Files API upload for multi-page PDFs
        temp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        try:
            temp_pdf.write(file_bytes)
            temp_pdf.close()
            
            if progress_callback:
                progress_callback("Uploading PDF to Gemini Files API...")
                
            uploaded_file = client.files.upload(
                file=temp_pdf.name,
                config=types.UploadFileConfig(mime_type="application/pdf")
            )
            
            # Wait for file processing if needed
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(1)
                uploaded_file = client.files.get(name=uploaded_file.name)

            if progress_callback:
                progress_callback("Reading handwriting and parsing pages with Gemini 3.6 Vision Engine...")

            response = client.models.generate_content(
                model=config.VISION_MODEL,
                contents=[ocr_prompt, uploaded_file]
            )
            
            # Clean up uploaded file from Gemini storage
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                pass
                
            if response.text and len(response.text.strip()) > 30:
                return response.text, []

        except Exception as e:
            if progress_callback:
                progress_callback(f"Files API fallback: {str(e)}")
        finally:
            if os.path.exists(temp_pdf.name):
                try:
                    os.remove(temp_pdf.name)
                except Exception:
                    pass

        # 2. Fallback: Digital text check
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            raw_text = ""
            for i, page in enumerate(reader.pages):
                t = page.extract_text()
                if t:
                    raw_text += f"--- [Page {i + 1}] ---\n" + t + "\n"
            if raw_text.strip():
                return raw_text, []
        except Exception:
            pass

        return "Unable to parse PDF text. Please ensure the PDF is valid.", []

    elif filename_lower.endswith((".png", ".jpg", ".jpeg", ".webp")):
        img = Image.open(io.BytesIO(file_bytes))
        ocr_text = run_multimodal_ocr_parallel(client, [img])
        return ocr_text, [img]

    else:
        return file_bytes.decode("utf-8", errors="ignore"), []

def run_multimodal_ocr_parallel(client, images):
    tasks = [(client, i, img) for i, img in enumerate(images)]
    results = [None] * len(images)
    max_workers = min(10, max(1, len(images)))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for idx, page_text in executor.map(process_single_page, tasks):
            results[idx] = page_text
    return "\n\n".join(results)

def process_single_page(args):
    client, idx, img = args
    ocr_prompt = "Transcribe handwritten text from this answer paper page line by line accurately."
    try:
        response = client.models.generate_content(
            model=config.VISION_MODEL,
            contents=[ocr_prompt, img]
        )
        return idx, f"--- [Page {idx + 1}] ---\n" + response.text
    except Exception as e:
        return idx, f"--- [Page {idx + 1}] ---\n(OCR Error: {str(e)})"
