# backend/ocr_engine.py

import asyncio
import winocr
from PIL import Image
from screen_capture import capture_screen, preprocess_for_ocr


def run_async(coro):
    """Helper to run async WinOCR calls synchronously."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)


def extract_text_from_image(pil_image):
    """
    Runs WinOCR on a PIL image.
    Returns extracted text as a string.
    """
    try:
        result = run_async(winocr.recognize_pil(pil_image, "en"))
        if result and hasattr(result, 'text'):
            return result.text.strip()
        return ""
    except Exception as e:
        print(f"[OCR Error] {e}")
        return ""


def extract_text_from_screen():
    """
    Main function called by scanner.
    Returns (text, raw_screenshot).
    """
    try:
        raw, _    = capture_screen()
        processed = preprocess_for_ocr(raw)
        text      = extract_text_from_image(processed)
        print(f"[OCR] Extracted {len(text)} characters")
        return text, raw
    except Exception as e:
        print(f"[OCR Error] {e}")
        return "", None


def extract_with_boxes(pil_image):
    """
    Returns word-level bounding boxes from WinOCR.
    Used by masking overlay to locate sensitive regions.
    Format matches what masking_overlay.py expects.
    """
    try:
        result = run_async(winocr.recognize_pil(pil_image, "en"))

        boxes = {
            'text':   [],
            'conf':   [],
            'left':   [],
            'top':    [],
            'width':  [],
            'height': [],
        }

        if not result or not hasattr(result, 'lines'):
            return boxes

        for line in result.lines:
            for word in line.words:
                boxes['text'].append(word.text)
                boxes['conf'].append(90)  # WinOCR doesn't give confidence scores — assume high
                boxes['left'].append(int(word.bounding_rect.x))
                boxes['top'].append(int(word.bounding_rect.y))
                boxes['width'].append(int(word.bounding_rect.width))
                boxes['height'].append(int(word.bounding_rect.height))

        return boxes

    except Exception as e:
        print(f"[OCR Boxes Error] {e}")
        return {'text': [], 'conf': [], 'left': [], 'top': [], 'width': [], 'height': []}