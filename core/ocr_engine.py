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

from pypdf import PdfReader, PdfWriter

def process_pdf_or_image(file_bytes, filename, start_page=1, end_page=None, api_key=None, progress_callback=None):
    """
    Processes uploaded file (PDF or Image).
    Allows selecting a specific page range (start_page to end_page) to save API vision tokens.
    First attempts zero-cost local PyPDF text extraction for typed/digital PDFs.
    Falls back to Gemini Files API Vision OCR for handwritten multi-page PDFs.
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
        # Local PDF Slicing to process only selected page range
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            total_pages = len(reader.pages)
            
            s_page = max(1, min(start_page, total_pages))
            e_page = total_pages if end_page is None else max(s_page, min(end_page, total_pages))
            
            # Slice PDF pages if partial range selected
            if s_page > 1 or e_page < total_pages:
                writer = PdfWriter()
                for p in range(s_page - 1, e_page):
                    writer.add_page(reader.pages[p])
                slice_buf = io.BytesIO()
                writer.write(slice_buf)
                file_bytes = slice_buf.getvalue()
                reader = PdfReader(io.BytesIO(file_bytes))
                if progress_callback:
                    progress_callback(f"📄 Sliced PDF to pages {s_page} to {e_page} of {total_pages}...")
        except Exception:
            pass

        # 1. OPTIMIZATION: Try zero-cost local PyPDF extraction first for digital/selectable text
        try:
            raw_text = ""
            for i, page in enumerate(reader.pages):
                t = page.extract_text()
                if t and len(t.strip()) > 30:
                    raw_text += f"--- [Page {i + 1}] ---\n" + t.strip() + "\n\n"
            
            # If significant digital text was extracted (e.g. topper copy or typed PDF), return immediately for ₹0 API cost!
            if raw_text and len(raw_text.strip()) > 200:
                if progress_callback:
                    progress_callback("⚡ Extracted digital PDF text locally (0 API cost)...")
                return raw_text, []
        except Exception:
            pass

        # 2. Gemini Files API Vision OCR for handwritten multi-page PDFs
        temp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        try:
            temp_pdf.write(file_bytes)
            temp_pdf.close()
            
            if progress_callback:
                progress_callback("Uploading handwritten PDF to Gemini Files API...")
                
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

        return "Unable to parse PDF text. Please ensure the PDF is valid.", []

    elif filename_lower.endswith((".png", ".jpg", ".jpeg", ".webp")):
        raw_img = Image.open(io.BytesIO(file_bytes))
        optimized_img = compress_and_resize_image(raw_img)
        ocr_text = run_multimodal_ocr_parallel(client, [optimized_img])
        return ocr_text, [optimized_img]

    else:
        return file_bytes.decode("utf-8", errors="ignore"), []

def compress_and_resize_image(img, max_dim=1400, quality=75):
    """
    Downscales document image resolution and compresses to JPEG format.
    Reduces visual patch token consumption per page from ~2,580 tokens down to ~512-768 tokens (70-80% token savings).
    """
    try:
        img_rgb = img.convert("RGB")
        img_rgb.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img_rgb.save(buf, format="JPEG", quality=quality, optimize=True)
        buf.seek(0)
        return Image.open(buf)
    except Exception:
        return img

def run_multimodal_ocr_parallel(client, images):
    optimized_images = [compress_and_resize_image(img) for img in images]
    tasks = [(client, i, img) for i, img in enumerate(optimized_images)]
    results = [None] * len(optimized_images)
    max_workers = min(10, max(1, len(optimized_images)))
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

