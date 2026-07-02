import sys
import os

# 1. Force Python to see the root directory immediately
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 2. Now perform standard application library imports
from PySide6.QtWidgets import QApplication
from frontend.controller import AppController
from frontend.ui_main import MainWindow


def apply_application_theme(app_instance):
    stylesheet_file = os.path.join(os.path.dirname(__file__), "frontend", "styles.qss")
    if os.path.exists(stylesheet_file):
        with open(stylesheet_file, "r", encoding="utf-8") as style_data:
            app_instance.setStyleSheet(style_data.read())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    controller = AppController()
    window = MainWindow(controller)
    apply_application_theme(app)
    
    window.show()
    sys.exit(app.exec())