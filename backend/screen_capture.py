# backend/screen_capture.py

import pyautogui
import cv2
import numpy as np
from PIL import Image

pyautogui.FAILSAFE = False

def capture_screen():
    """Captures full screen. Returns PIL image and numpy BGR array."""
    screenshot = pyautogui.screenshot()
    frame      = np.array(screenshot)
    frame_bgr  = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    return screenshot, frame_bgr

def preprocess_for_ocr(pil_image):
    """
    Light preprocessing for WinOCR.
    WinOCR handles color images well — just mild sharpening.
    """
    img = np.array(pil_image)

    # Mild upscale for small text
    w = int(img.shape[1] * 1.5)
    h = int(img.shape[0] * 1.5)
    resized = cv2.resize(img, (w, h), interpolation=cv2.INTER_CUBIC)

    return Image.fromarray(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))