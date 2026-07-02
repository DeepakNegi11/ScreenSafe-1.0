from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame
from PySide6.QtCore import Qt, Property, QPropertyAnimation
from PySide6.QtGui import QPainter, QColor, QBrush

class ModernToggle(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 30)
        self._checked = False
        self._position = 3

    @Property(int)
    def position(self): return self._position

    @position.setter
    def position(self, pos):
        self._position = pos
        self.update()

    def isChecked(self): return self._checked

    def setChecked(self, checked):
        self._checked = checked
        self.animate()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._checked = not self._checked
            self.animate()
            if hasattr(self, 'clicked_callback'):
                self.clicked_callback(self._checked)

    def animate(self):
        self.animation = QPropertyAnimation(self, b"position")
        self.animation.setDuration(180)
        self.animation.setStartValue(self.position)
        self.animation.setEndValue(33 if self._checked else 3)
        self.animation.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # NEW WARM COLORS: Terracotta when ON, Light beige when OFF
        bg_color = QColor("#D48C70") if self._checked else QColor("#D9D0C7")
        
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 15, 15)
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(self._position, 3, 24, 24)
        painter.end()

class StatCard(QFrame):
    def __init__(self, title, initial_val, parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        self.lbl_val = QLabel(str(initial_val))
        # Changed value color to Terracotta
        self.lbl_val.setStyleSheet("font-size: 22px; font-weight: bold; color: #D48C70;")
        self.lbl_val.setAlignment(Qt.AlignCenter)
        
        self.lbl_title = QLabel(title)
        # Changed title color to Warm Gray
        self.lbl_title.setStyleSheet("color: #7A726D; font-size: 11px; font-weight: 500;")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.lbl_val)
        layout.addWidget(self.lbl_title)

    def update_value(self, val):
        self.lbl_val.setText(str(val))