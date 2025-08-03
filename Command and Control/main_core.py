import sys
import json
from pathlib import Path
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, Qt
from PyQt6.QtGui import QIcon, QPixmap, QFont, QPalette, QColor, QKeySequence
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QMainWindow, QMessageBox
)

## Import custom widgets
from control_buttons import ControlButtons
from clickable_label import ClickableLabel as QLabel

# Paths
ASSETS_PATH = Path(__file__).resolve().parent / "assets"
ICON_PATH   = ASSETS_PATH / "icons"
LOGO_PATH   = ASSETS_PATH / "images" / "AMBOT Logo Transparent BG 2.png"
THEME_PATH  = ASSETS_PATH / "theme.json"

def load_theme(theme_file):
    with open(theme_file, "r") as f:
        return json.load(f)

def apply_palette(app, theme):
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,           QColor(theme["window"]))
    palette.setColor(QPalette.ColorRole.WindowText,       QColor(theme["windowText"]))
    palette.setColor(QPalette.ColorRole.Base,             QColor(theme["base"]))
    palette.setColor(QPalette.ColorRole.AlternateBase,    QColor(theme["alternateBase"]))
    palette.setColor(QPalette.ColorRole.ToolTipBase,      QColor(theme["toolTipBase"]))
    palette.setColor(QPalette.ColorRole.ToolTipText,      QColor(theme["toolTipText"]))
    palette.setColor(QPalette.ColorRole.Text,             QColor(theme["text"]))
    palette.setColor(QPalette.ColorRole.Button,           QColor(theme["button"]))
    palette.setColor(QPalette.ColorRole.ButtonText,       QColor(theme["buttonText"]))
    palette.setColor(QPalette.ColorRole.BrightText,       QColor(theme["brightText"]))
    palette.setColor(QPalette.ColorRole.Link,             QColor(theme["link"]))
    palette.setColor(QPalette.ColorRole.Highlight,        QColor(theme["highlight"]))
    palette.setColor(QPalette.ColorRole.HighlightedText,  QColor(theme["highlightedText"]))
    app.setPalette(palette)

def apply_font(app, theme):
    font = QFont(theme.get("font_family", "Etna Sans Serif"), theme.get("font_size", 10))
    app.setFont(font)

class CustomTitleBar(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self._parent = parent
        
        self.setFixedHeight (36)
        self.setStyleSheet  ("background-color: #111a5b;")  # Main background color

        h_layout = QHBoxLayout      (self)
        h_layout.setContentsMargins (10, 0, 10, 0)  
        h_layout.setSpacing         (5)            
              
        ### LOGO
        logo    = QLabel()
        pixmap  = QPixmap(str(LOGO_PATH))
        
        if pixmap.isNull():
            print(f"WARNING: Logo image not found at: {LOGO_PATH}")
        else:
            pixmap = pixmap.scaled(80, 64, 
                                   Qt.AspectRatioMode.KeepAspectRatio, 
                                   Qt.TransformationMode.SmoothTransformation
                                   )
        
        logo.setPixmap       (pixmap)
        logo.setFixedSize    (80, 32)
        logo.setStyleSheet   ("background: transparent;")
        h_layout.addWidget   (logo, alignment = Qt.AlignmentFlag.AlignVCenter)
        logo.setCursor       (Qt.CursorShape.PointingHandCursor)
        logo.setFocusPolicy  (Qt.FocusPolicy.NoFocus)
        logo.clicked.connect (self.on_logo_clicked)
        
        h_layout.addStretch(1)

        ### CENTER TEXT
        center_label = QLabel       ("COMMAND AND CONTROL")
        center_label.setStyleSheet  ("color: white; font-size: 15px; font-family: 'Etna Sans Serif'; letter-spacing: 1px; background: transparent;")
        h_layout.addWidget          (center_label, alignment = Qt.AlignmentFlag.AlignCenter)
        h_layout.addStretch(1)

        ### CIRCLE WINDOW CONTROL BUTTONS
        def make_circle_btn(color, tooltip):
            btn = QPushButton   ("")
            btn.setCursor       (Qt.CursorShape.PointingHandCursor)
            btn.setFocusPolicy  (Qt.FocusPolicy.NoFocus)
            btn.setFixedSize    (16, 16)
            btn.setStyleSheet   (f"border-radius:8px; background-color:{color}; border:none;")
            btn.setToolTip      (tooltip)
            
            return btn

        close_btn = make_circle_btn ("#D32F2F", "Close")
        max_btn   = make_circle_btn ("#FBC02D", "Maximize/Restore")
        min_btn   = make_circle_btn ("#388E3C", "Minimize")
        
        close_btn.clicked.connect   (self.on_close)
        max_btn.clicked.connect     (self.on_maximize)
        min_btn.clicked.connect     (self.on_minimize)
        h_layout.addWidget          (close_btn)
        h_layout.addWidget          (max_btn)
        h_layout.addWidget          (min_btn)
        self.setLayout              (h_layout)
        
        self._dragActive = False
    
    def on_logo_clicked(self):
        self._parent.LOGO_pressed()
        
    def on_close(self):
        self._parent.request_exit()

    def on_maximize(self):
        if self._parent.isMaximized():
            self._parent.showNormal()
        else:
            self._parent.showMaximized()

    def on_minimize(self):
        self._parent.showMinimized()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._startPos      = event.globalPosition().toPoint()
            self._dragActive    = True
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
    def __init__(self, theme):
        super().__init__()
        
        # Frameless window, own custom title bar
        self.setWindowFlag  (Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle ("AMBOT Command and Control")
        self.setWindowIcon  (QIcon(str(ICON_PATH / 'AMBOT_main_plain_icon_w.ico')))
        #self.setGeometry    (100, 100, 1200, 700)
        
        # Layout with title bar and main area
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.title_bar = CustomTitleBar(self)
        main_layout.addWidget(self.title_bar)

        # Main body (replace this with your functional widgets)
        body = QWidget()
        body.setStyleSheet("background-color: #222;")
        main_layout.addWidget(body)

        self.setCentralWidget(main_widget)

        # Theme ref
        self.theme = theme

        # Key bindings
        self.installEventFilter(self)
        
        self.showFullScreen()
        
    def LOGO_pressed(self):
        QMessageBox.information(
            self, "AMBOT Adaptive Machine Bot for Operations and Tasks",
            "Copyright 2025. All rights reserved.\n\n An advanced autonomous prototype robot equipped to perform versatile operational tasks and adaptive exploratory functions.\n\nSofware Developed by Francis Mike John Camogao, 2025.",
        )

    # ESC or window close
    def request_exit(self):
        reply = QMessageBox.question(
            self, 'Exit',
            'Are you sure you want to exit?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.close()

    # Allow ESC to trigger close
    def eventFilter(self, obj, event):
        if event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self.request_exit()
                return True
            elif event.key() == Qt.Key.Key_F11:
                # F11 toggles maximized/fullscreen
                if self.isFullScreen():
                    self.showNormal()
                else:
                    self.showFullScreen()
                return True
            
        return super().eventFilter(obj, event)

def main():
    app = QApplication(sys.argv)
    QApplication.setStyle("Fusion")
    theme = load_theme(THEME_PATH)
    apply_palette(app, theme)
    apply_font(app, theme)

    dashboard = TelemetryDashboard(theme)
    dashboard.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

