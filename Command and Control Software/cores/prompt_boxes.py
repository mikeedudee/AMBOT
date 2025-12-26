from PyQt6.QtWidgets import QMessageBox

class Dialouge_Boxes:
    @staticmethod
    def request_exit(parent):
        reply = QMessageBox.question(
            parent, 'Exit',
            'Are you sure you want to exit?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

    def LOGO_pressed(parent):
        QMessageBox.information(
            parent, "Adaptive Machine Bot for Operations and Tasks — Command and Control",
            "Copyright 2025 AMBOT. All rights reserved.\n\nAn advanced autonomous prototype robot equipped to perform versatile operational tasks and adaptive exploratory functions. This sofware is built dedicatedly for the AMBOT Robot for sending Commands and Control it remotely.\n\nSofware Developed by Francis Mike John Camogao.\n\nCONTACTS:\nEmail: francismikejohn.camogao@gmail.com\nGitHub: https://github.com/mikeedudee\n\nBuild Version: 1.2.7",
        )
        
    def No_COMPORT_Selected(parent):
        QMessageBox.critical(
            parent, "Connection Error",
            "No COM port selected. Please select a COM port to connect.",
            QMessageBox.StandardButton.Ok
        )
        
    def Connection_Disconnected(parent, error):
        QMessageBox.information(
            parent, "Connection Error",
            "Failed to connect to the AMBOT Robot. Failed to connect to the COM port.\n\nError: " + str(error),
            QMessageBox.StandardButton.Ok
        )