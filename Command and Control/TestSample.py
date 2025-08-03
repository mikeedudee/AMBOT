import sys
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap, QFont
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QMainWindow, QMessageBox
)

ASSETS_PATH = Path(__file__).resolve().parent / "assets"
ICON_PATH   = ASSETS_PATH / "icons"
LOGO_PATH   = ASSETS_PATH / "AMBOT_logo.png"

class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._parent = parent
        self.setFixedHeight(36)
        # Set the background color exactly
        self.setStyleSheet("background-color: #141E61;")

        # Main horizontal layout, no margins or spacing
        h_layout = QHBoxLayout(self)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)

        # Left: Logo
        logo = QLabel()
        pixmap = QPixmap(str(LOGO_PATH))
        if not pixmap.isNull():
            pixmap = pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        logo.setPixmap(pixmap)
        logo.setFixedWidth(40)
        h_layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignVCenter)

        # "AMBOT" label, bold
        ambot_label = QLabel("AMBOT")
        ambot_label.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
        ambot_label.setStyleSheet("color: white; padding-left: 2px; padding-right: 12px;")
        h_layout.addWidget(ambot_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Spacer between left group and center text
        h_layout.addStretch(1)

        # Center text
        center_label = QLabel("COMMAND AND CONTROL")
        center_label.setFont(QFont("Segoe UI", 13))
        center_label.setStyleSheet("color: white; letter-spacing: 1px;")
        h_layout.addWidget(center_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Spacer between center and right controls
        h_layout.addStretch(1)

        # Window control buttons (right, round, floating)
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 16, 0)  # right padding for aesthetics
        button_layout.setSpacing(8)

        def make_circle_btn(color, tooltip):
            btn = QPushButton("")
            btn.setFixedSize(18, 18)
            btn.setStyleSheet(f"""
                QPushButton {{
                    border-radius: 9px;
                    background-color: {color};
                    border: none;
                }}
                QPushButton:hover {{
                    filter: brightness(50%);
                }}
            """)
            btn.setToolTip(tooltip)
            return btn

        close_btn   = make_circle_btn("#D32F2F", "Close")
        orange_btn  = make_circle_btn("#FF9800", "Maximize/Restore")
        green_btn   = make_circle_btn("#4CAF50", "Minimize")

        close_btn.clicked.connect(self.on_close)
        orange_btn.clicked.connect(self.on_maximize)
        green_btn.clicked.connect(self.on_minimize)

        # Add buttons, rightmost order: red, orange, green
        button_layout.addWidget(close_btn)
        button_layout.addWidget(orange_btn)
        button_layout.addWidget(green_btn)

        # Right group widget to keep buttons right-aligned
        right_widget = QWidget()
        right_widget.setLayout(button_layout)
        h_layout.addWidget(right_widget, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.setLayout(h_layout)
        self._dragActive = False

    def on_close(self):
        self._parent.request_exit()

    def on_maximize(self):
        if self._parent.isMaximized():
            self._parent.showNormal()
        else:
            self._parent.showMaximized()

    def on_minimize(self):
        self._parent.showMinimized()

    # Enable window dragging
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._startPos = event.globalPosition().toPoint()
            self._dragActive = True
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self, "_dragActive", False):
            delta = event.globalPosition().toPoint() - self._startPos
            self._parent.move(self._parent.pos() + delta)
            self._startPos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._dragActive = False
        super().mouseReleaseEvent(event)

class TelemetryDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("AMBOT Command and Control")
        self.setWindowIcon(QIcon(str(ICON_PATH / 'AMBOT_main_plain_icon_w.ico')))
        self.setGeometry(100, 100, 1200, 700)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.title_bar = CustomTitleBar(self)
        main_layout.addWidget(self.title_bar)

        # Main area (just a black area for now)
        body = QWidget()
        body.setStyleSheet("background-color: #222;")
        main_layout.addWidget(body)

        self.setCentralWidget(main_widget)
        self.installEventFilter(self)

    # Exit confirmation on close (ESC or red button)
    def request_exit(self):
        reply = QMessageBox.question(
            self, 'Exit',
            'Are you sure you want to exit?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.close()

    def eventFilter(self, obj, event):
        if event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self.request_exit()
                return True
            elif event.key() == Qt.Key.Key_F11:
                if self.isFullScreen():
                    self.showNormal()
                else:
                    self.showFullScreen()
                return True
        return super().eventFilter(obj, event)

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = TelemetryDashboard()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
