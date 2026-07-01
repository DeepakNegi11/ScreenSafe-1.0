# backend/app.py

from flask import Flask, jsonify
from flask_cors import CORS
from scanner import start_scanner, get_state
from sensitive_detector import detect_sensitive_data
from config import FLASK_PORT
import threading

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/status", methods=["GET"])
def status():
    return jsonify(get_state())

@app.route("/recording", methods=["GET"])
def recording():
    state = get_state()
    return jsonify(state["recording_status"])

@app.route("/detection", methods=["GET"])
def detection():
    state = get_state()
    return jsonify(state["detection_result"])

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "ScreenSafe Python Engine",
        "threads": threading.active_count()
    })

@app.route("/test", methods=["GET"])
def test_detection():
    test_text = "Your OTP is 829401. Card: 4111 1111 1111 1111 CVV: 234. Password: Secr3t@123"
    result = detect_sensitive_data(test_text)
    return jsonify({
        "test_input": test_text,
        "result": result
    })

@app.route("/scancount", methods=["GET"])
def scancount():
    state = get_state()
    return jsonify({"scan_count": state["scan_count"]})

if __name__ == "__main__":
    print("[ScreenSafe] Starting Python detection engine...")
    print("[ScreenSafe] Starting scanner thread...")
    start_scanner()
    print("[ScreenSafe] Scanner thread launched. Starting Flask...")
    app.run(port=FLASK_PORT, debug=False, threaded=True)