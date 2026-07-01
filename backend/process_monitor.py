# backend/process_monitor.py

import psutil
from config import RECORDING_PROCESSES

def get_running_processes():
    """Returns a list of all currently running process names (lowercase)."""
    running = []
    for proc in psutil.process_iter(['name']):
        try:
            running.append(proc.info['name'].lower())
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return running

def is_screen_being_recorded():
    """
    Returns a dict:
    {
        "recording": True/False,
        "detected_app": "zoom.exe" or None
    }
    """
    running = get_running_processes()
    for proc in RECORDING_PROCESSES:
        if proc.lower() in running:
            return {"recording": True, "detected_app": proc}
    return {"recording": False, "detected_app": None}


if __name__ == "__main__":
    result = is_screen_being_recorded()
    print(result)