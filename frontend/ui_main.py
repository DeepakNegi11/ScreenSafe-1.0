from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget, QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt
from frontend.ui_pages import HomePage, SettingsPage, AboutPage

class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("ScreenSafe")
        self.resize(960, 640)

        self.setup_tray_icon()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar configuration
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(210)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 20)
        sidebar_layout.setAlignment(Qt.AlignTop)

        self.btn_home = QPushButton("📊  Dashboard")
        self.btn_settings = QPushButton("⚙️  Settings")
        self.btn_about = QPushButton("ℹ️  About Engine")
        self.nav_buttons = [self.btn_home, self.btn_settings, self.btn_about]
        
        for btn in self.nav_buttons:
            btn.setProperty("class", "nav-btn")
            btn.setCheckable(True)
            sidebar_layout.addWidget(btn)
        self.btn_home.setChecked(True)

        # Main page stacking system
        self.pages = QStackedWidget()
        self.pages.addWidget(HomePage(self.controller))
        self.pages.addWidget(SettingsPage())
        self.pages.addWidget(AboutPage())

        self.btn_home.clicked.connect(lambda: self.navigate_to_index(0))
        self.btn_settings.clicked.connect(lambda: self.navigate_to_index(1))
        self.btn_about.clicked.connect(lambda: self.navigate_to_index(2))

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.pages)

    def navigate_to_index(self, index):
        for idx, btn in enumerate(self.nav_buttons):
            btn.setChecked(idx == index)
        self.pages.setCurrentIndex(index)

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        fallback_icon = QIcon.fromTheme("security-high", QIcon())
        self.tray_icon.setIcon(fallback_icon)
        
        menu = QMenu()
        open_action = QAction("Maximize Workspace", self)
        open_action.triggered.connect(self.showNormal)
        quit_action = QAction("Terminate Application", self)
        quit_action.triggered.connect(self.terminate_entire_app)
        
        menu.addAction(open_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def closeEvent(self, event):
        # Minimize to system tray instead of destroying the process
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "ScreenSafe Active Shield",
            "Privacy intercept parsing continues active in system task loops.",
            QSystemTrayIcon.Information,
            2500
        )

    def terminate_entire_app(self):
        self.controller.shutdown()
        self.tray_icon.hide()
        QApplication.quit()