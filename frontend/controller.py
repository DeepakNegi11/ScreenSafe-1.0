import time
from PySide6.QtCore import QObject, Signal, QThread

# Import the backend module directly
import backend.scanner as scanner

class ScannerWorker(QThread):
    status_changed = Signal(str, str)
    log_added = Signal(str)
    stats_updated = Signal(dict)

    def __init__(self):
        super().__init__()
        self._is_running = False
        
        # Internal stat trackers
        self._last_scan_count = 0
        self._session_threats = 0
        self._last_detection_time = "None"

    def run(self):
        self._is_running = True
        self.status_changed.emit("active", "🟢 Protection Enabled - Scanning Active")
        self.log_added.emit("Worker thread started: Engaging backend engine...")
        
        # 1. Start the backend engine natively!
        # Your scanner.py already puts this in a background thread for us.
        try:
            scanner.start_scanner()
        except Exception as e:
            self.log_added.emit(f"Failed to start scanner: {str(e)}")

        # 2. UI Polling loop
        while self._is_running:
            try:
                state = scanner.get_state() or {}
                
                scan_count = state.get("scan_count", self._last_scan_count)
                detection_result = state.get("detection_result", {})
                risk_level = detection_result.get("risk_level", "LOW")
                
                # If a threat is detected, log it and update trackers
                if risk_level in ["MEDIUM", "HIGH", "CRITICAL"]:
                    self._last_detection_time = time.strftime('%H:%M:%S')
                    self._session_threats += len(detection_result.get("findings", []))
                    
                    # Prevent log spam by only logging when the scan count changes
                    if scan_count != self._last_scan_count:
                        self.log_added.emit(f"[{self._last_detection_time}] Threat Intercepted: {risk_level} Risk")

                self._last_scan_count = scan_count
                
                # Package it perfectly for the UI StatCards
                ui_stats = {
                    "hidden_today": scan_count,
                    "session_detections": self._session_threats,
                    "uptime": "Active",
                    "last_detection": self._last_detection_time
                }
                
                self.stats_updated.emit(ui_stats)
            except Exception as e:
                pass
            
            time.sleep(0.25)

    def stop(self):
        self._is_running = False
        
        # 🛑 THE MAGIC FIX: We officially tell the backend to stop its while loop!
        try:
            scanner.stop_scanner()
        except Exception:
            pass
            
        self.status_changed.emit("idle", "🔴 Protection Disabled - Idle")
        self.log_added.emit("Worker thread stopped: Backend scanning paused.")

class AppController:
    def __init__(self):
        self.worker = ScannerWorker()

    def toggle_protection(self, is_active):
        if is_active:
            self.worker.start()
        else:
            self.worker.stop()

    def shutdown(self):
        self.worker.stop()
        self.worker.wait()