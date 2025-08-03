from PyQt6.QtWidgets import QWidget, QPushButton, QGridLayout

class ControlButtons(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)
        self.buttons = {}
        btn_labels = [
            "KEYBOARD CONTROL", "REMOTE CONTROLLER", "AMBOT R-CONTROLLER", "MOBILE APP",
            "VOICE MODE", "FULLY AUTONOMOUS", "CHAT MODE", "GPS",
            "Manual Mode", "Automatic Mode", "SAVE SYSTEM STATUS", "COM PORT", 
            "SYSTEM RESET", "BAUD RATE", "LOGOUT", "EXIT"
        ]
        for i, label in enumerate(btn_labels):
            btn = QPushButton(label)
            btn.setFixedHeight(40)
            layout.addWidget(btn, i // 4, i % 4)
            self.buttons[label] = btn