# backend/scanner.py

import time
import threading
from process_monitor import is_screen_being_recorded
from ocr_engine import extract_text_from_screen
from sensitive_detector import detect_sensitive_data
from masking_overlay import apply_mask_overlay
from config import SCAN_INTERVAL, FORCE_SCAN

scan_state = {
    "recording_status": {"recording": False, "detected_app": None},
    "last_scan_text":   "",
    "detection_result": {
        "is_sensitive": False,
        "findings":     [],
        "risk_level":   "LOW"
    },
    "scan_count":       0,
    "last_scan_time":   None,
}

_lock       = threading.Lock()
_stop_event = threading.Event()


def run_scan_loop():
    while not _stop_event.is_set():
        try:
            rec_status = is_screen_being_recorded()
            if FORCE_SCAN:
                rec_status = {"recording": True, "detected_app": "force_scan_mode"}

            with _lock:
                scan_state["recording_status"] = rec_status
                scan_state["last_scan_time"]   = time.strftime("%H:%M:%S")

            if rec_status["recording"]:
                print(f"[Scanner] Scan #{scan_state['scan_count'] + 1}...")

                text, raw = extract_text_from_screen()
                print(f"[Scanner] {len(text)} chars extracted")

                result = detect_sensitive_data(text)
                print(f"[Scanner] {result['risk_level']} — "
                      f"{len(result['findings'])} finding(s)")

                with _lock:
                    scan_state["last_scan_text"]   = text[:500]
                    scan_state["detection_result"] = result
                    scan_state["scan_count"]      += 1

                apply_mask_overlay(result["is_sensitive"], screenshot=raw)

        except Exception as e:
            print(f"[Scanner Error] {e}")
            import traceback
            traceback.print_exc()

        time.sleep(SCAN_INTERVAL)


def start_scanner():
    _stop_event.clear()
    threading.Thread(target=run_scan_loop, daemon=True).start()
    print("[ScreenSafe] Scanner started.")
    print(f"[ScreenSafe] FORCE_SCAN    = {FORCE_SCAN}")
    print(f"[ScreenSafe] SCAN_INTERVAL = {SCAN_INTERVAL}s")


def stop_scanner():
    _stop_event.set()


def get_state():
    with _lock:
        return dict(scan_state)