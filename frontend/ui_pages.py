from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QListWidget, QCheckBox, QGridLayout
from PySide6.QtCore import Qt
from frontend.ui_components import ModernToggle, StatCard

class HomePage(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        title = QLabel("ScreenSafe")
        title.setProperty("class", "h1")
        subtitle = QLabel("Real-Time Screen Privacy Protection")
        subtitle.setProperty("class", "subtitle")
        
        desc = QLabel("ScreenSafe watches active frame captures natively on device, checking for strings matching expressions like authentication credentials or financial keys. Whenever a matches condition triggers, processing applies an obstructive mask.")
        desc.setWordWrap(True)
        # Updated description to warm gray
        desc.setStyleSheet("color: #7A726D; max-width: 700px; line-height: 1.4;")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(desc)

        control_layout = QHBoxLayout()
        self.toggle = ModernToggle()
        self.toggle.clicked_callback = self.handle_toggle
        
        self.lbl_status = QLabel("🔴 Protection Disabled - Idle")
        self.lbl_status.setProperty("class", "h2")
        
        control_layout.addWidget(self.toggle)
        control_layout.addWidget(self.lbl_status)
        control_layout.addStretch()
        layout.addLayout(control_layout)

        stats_layout = QGridLayout()
        self.card_hidden = StatCard("Total Scans Run", 0)
        self.card_session = StatCard("Active Match Items", 0)
        self.card_uptime = StatCard("System State", "Offline")
        self.card_last = StatCard("Last Target Event", "Never")
        
        stats_layout.addWidget(self.card_hidden, 0, 0)
        stats_layout.addWidget(self.card_session, 0, 1)
        stats_layout.addWidget(self.card_uptime, 0, 2)
        stats_layout.addWidget(self.card_last, 0, 3)
        layout.addLayout(stats_layout)

        log_label = QLabel("Internal Engine Pipeline Activity Log")
        log_label.setProperty("class", "h2")
        layout.addWidget(log_label)
        
        self.log_widget = QListWidget()
        layout.addWidget(self.log_widget)

        self.controller.worker.status_changed.connect(self.update_status_display)
        self.controller.worker.log_added.connect(self.append_log_message)
        self.controller.worker.stats_updated.connect(self.refresh_stats_display)

    def handle_toggle(self, is_checked):
        self.controller.toggle_protection(is_checked)

    def update_status_display(self, status_type, message):
        self.lbl_status.setText(message)
        # Updated to Warm Sage Green (active) and Soft Rose Red (idle)
        self.lbl_status.setStyleSheet("color: #6B9080;" if status_type == "active" else "color: #D96C6C;")

    def append_log_message(self, message):
        self.log_widget.insertItem(0, message)
        if self.log_widget.count() > 100:
            self.log_widget.takeItem(self.log_widget.count() - 1)

    def refresh_stats_display(self, stats):
        self.card_hidden.update_value(stats["hidden_today"])
        self.card_session.update_value(stats["session_detections"])
        self.card_uptime.update_value(stats["uptime"])
        self.card_last.update_value(stats["last_detection"])

class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(12)
        
        title = QLabel("Configurations Profile")
        title.setProperty("class", "h1")
        layout.addWidget(title)

        options = [
            "Start automatically on system logon", 
            "Minimize to System Tray on close action", 
            "Audible alerts upon redaction execution hooks", 
            "Filter Passwords", "Filter One-Time Passwords (OTPs)", 
            "Filter Cloud Access Tokens & API Keys", "Filter Payment Cards & Financial Data"
        ]
        for opt in options:
            cb = QCheckBox(opt)
            cb.setChecked(True)
            layout.addWidget(cb)

class AboutPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setAlignment(Qt.AlignTop)
        
        title = QLabel("About ScreenSafe")
        title.setProperty("class", "h1")
        layout.addWidget(title)

        content = QLabel(
            "\nScreenSafe Platform Engine Architecture — Client Edition\n\n"
            "An advanced modular UI built for client processing, which interfaces directly "
            "with memory structures for localized computer vision parsing.\n\n"
            "DATA PRIVACY NOTE:\n"
            "All capture processing runs isolated inside device memory blocks. Zero telemetry profiles, "
            "screen frames, or metadata records get transmitted outwards over standard cloud configurations."
        )
        content.setWordWrap(True)
        # Updated to Warm Gray
        content.setStyleSheet("line-height: 1.6; color: #5C544F;")
        layout.addWidget(content)