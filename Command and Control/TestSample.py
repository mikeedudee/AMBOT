from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt6.QtCore import QSize
import sys

class BoxDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("systemStatusBox")
        self.setMinimumSize(QSize(400, 200))  # Force space

    def sizeHint(self):
        return QSize(400, 200)

app = QApplication(sys.argv)
main = QWidget()
main.setStyleSheet("")  # REMOVE all styles from parent!

layout = QVBoxLayout(main)
box = BoxDemo()
layout.addWidget(box)

# Set box style only
box.setStyleSheet("""
    QWidget#systemStatusBox {
        background-color: #FBC02D;
        border-radius: 18px;
        border: 6px solid #222;
    }
""")

main.show()
app.exec()