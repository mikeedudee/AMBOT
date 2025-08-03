# system_status.py

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy
from PyQt6.QtGui import QColor, QPainter, QFont
from PyQt6.QtCore import Qt, QSize

class StatusIndicator(QWidget):
    def __init__(self, label_text, working=False, parent=None):
        super().__init__(parent)
        self.working = working
        self.label = QLabel(label_text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.label.setFont(QFont("Etna Sans Serif", 10, QFont.Weight.Bold))
        self.setFixedSize(30, 30)

    def set_status(self, working):
        self.working = working
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        # RED if not working (0), GREEN if working (1)
        color = QColor("#3AE374") if self.working else QColor("#D32F2F")
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        radius = min(self.width(), self.height()) // 2 - 4
        painter.drawEllipse((self.width()-2*radius)//2, (self.height()-2*radius)//2, 2*radius, 2*radius)

class SystemStatusWidget(QWidget):
    def __init__(self, sensor_labels, servo_labels, parent=None):
        super().__init__(parent)
        self.setObjectName("systemStatusBox")
        self.sensor_labels = sensor_labels
        self.servo_labels = servo_labels

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)  # Padding inside box
        main_layout.setSpacing(10)

        # Title
        title = QLabel("SYSTEM STATUS")
        title.setFont(QFont("Etna Sans Serif", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # --- SENSORS: column layout for each sensor ---
        sensor_row = QHBoxLayout()
        self.sensor_indicators = []
        for label in self.sensor_labels:
            col = QVBoxLayout()
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            lbl.setFont(QFont("Etna Sans Serif", 10, QFont.Weight.Bold))
            indicator = StatusIndicator("")
            col.addWidget(lbl)
            col.addWidget(indicator, alignment=Qt.AlignmentFlag.AlignHCenter)
            self.sensor_indicators.append(indicator)
            sensor_widget = QWidget()
            sensor_widget.setLayout(col)
            sensor_row.addWidget(sensor_widget)
        main_layout.addLayout(sensor_row)

        # --- SERVOS: column layout for each servo ---
        servo_row = QHBoxLayout()
        self.servo_indicators = []
        for label in self.servo_labels:
            col = QVBoxLayout()
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            lbl.setFont(QFont("Etna Sans Serif", 10, QFont.Weight.Bold))
            indicator = StatusIndicator("")
            col.addWidget(lbl)
            col.addWidget(indicator, alignment=Qt.AlignmentFlag.AlignHCenter)
            self.servo_indicators.append(indicator)
            servo_widget = QWidget()
            servo_widget.setLayout(col)
            servo_row.addWidget(servo_widget)
        main_layout.addLayout(servo_row)

        # Appearance
        self.setStyleSheet("""
            QWidget#systemStatus {
                background-color: #191C20;
                border-radius: 14px;
                border: 2px solid #222;
            }
            QLabel {
                color: white;
            }
        """)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def set_status(self, sensor_states, servo_states):
        """Set status from list of bool/int (1=on/green, 0=off/red)"""
        for ind, state in zip(self.sensor_indicators, sensor_states):
            ind.set_status(bool(state))
        for ind, state in zip(self.servo_indicators, servo_states):
            ind.set_status(bool(state))

    def minimumSizeHint(self):
        return QSize(400, 150)
