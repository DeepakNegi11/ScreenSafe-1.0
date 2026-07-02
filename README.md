# ScreenSafe

ScreenSafe is a native desktop utility designed to provide real-time screen privacy protection. It continuously monitors on-screen text via a localized computer vision pipeline, checks for sensitive data strings matching specified criteria (such as credentials, API keys, or financial markers), and automatically applies a visual mask to obscure that data from accidental exposure or unauthorized recording.

## Features

* **Localized On-Device Processing**: Screen monitoring and Optical Character Recognition (OCR) parsing run completely in-memory locally. No data telemetry or screen contents are transmitted externally.
* **Warm, Minimalist User Interface**: A clean, accessible light-theme dashboard engineered with PySide6 for statistics viewing, toggling system protection, configuration profiling, and observing live pipeline engine logs.
* **Dual-Threaded Safe Architecture**: Separates the UI operational loop from the intensive core scanning and text verification threads to guarantee application performance and crash resilience.
* **Adaptive Data Redaction**: Dynamically handles data patterns across split tokens (such as credit card blocks spaced out as distinct chunks) and automatically updates obstructive overlays when protection parameters toggle.

## Project Structure

text
├── main.py                    # Application entry point
├── requirements.txt           # Python dependency specifications
├── backend/
│   ├── __init__.py
│   ├── config.py              # Configuration values, intervals, and flag limits
│   ├── process_monitor.py     # Recording status tracking structures
│   ├── ocr_engine.py          # Screen text extraction engine
│   ├── sensitive_detector.py  # Validation and pattern classification scripts
│   ├── masking_overlay.py     # Multi-threaded Tkinter mask creation logic
│   └── scanner.py             # Core daemon thread orchestration engine
└── frontend/
    ├── __init__.py
    ├── controller.py          # State coordination between PySide6 and backend
    ├── styles.qss             # Unified global stylesheet
    ├── ui_components.py       # Reusable customized PySide6 components 
    └── ui_pages.py            # Home, Settings, and About page templates



## System Requirements

* Python 3.9 or higher
* Operating System: Windows or macOS (Linux environments may require system-level Tkinter and X11 packages for display tracking)

## Dependencies

The core framework leverages the following primary packages:

* **PySide6**: Framework managing window states, custom layouts, and thread signal communication.
* **PyAutoGUI**: Handles system-level screenshot captures for structural frame processing.
* **Pillow (PIL)**: Provides underlying canvas scaling and dimensional processing.
* **OCR Platform**: Localized parsing engine (e.g., pytesseract or easyocr) as integrated via the backend ocr module.

## Installation

1. Clone the repository to your local workspace directory.
2. Navigate into the root path of the project.
3. Install the required libraries using pip:


pip install -r requirements.txt



*Note: Ensure your preferred OCR system binaries are properly added to your environment path parameters if your chosen engine requires a localized installer setup.*

## Usage

To start the ScreenSafe interface and initialize the processing engines, execute the main runtime file from your terminal:


python main.py



### Protection Toggle Functionality

* **Active Status**: Toggling protection to the ON position clears pause markers, launches the background scanning pipeline loop, and wakes the window verification threat-watcher.
* **Idle Status**: Turning protection to the OFF position instantly suspends image capture processes, halts processing sequences to minimize hardware utility overhead, and wipes any remaining masking overlays immediately from the active display layer.

