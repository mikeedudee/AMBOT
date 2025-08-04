from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QGridLayout, QSizePolicy, QGraphicsDropShadowEffect,
    QDialog, QHBoxLayout, QComboBox, QPushButton
)
from PyQt6.QtCore import Qt, QTimer, QEvent, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QPushButton, QComboBox
import serial.tools.list_ports
import serial
import json
import os
from cores import Dialouge_Boxes, ClickableLabel as QLabel

# --- Persistent Settings Management ---

SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".my_serial_settings.json")

DEFAULT_SETTINGS = {
    "baud_rate": "9600",
    "data_bits": "8",
    "parity": "None",
    "stop_bits": "1",
    "flow_control": "None",
    "send_as": "Text"
}

def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                data        = json.load(f)
                settings    = DEFAULT_SETTINGS.copy()
                settings.update({k: v for k, v in data.items() if k in settings})
                
                return settings
            
    except Exception:
        pass
    
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f)
    except Exception:
        pass

serial_settings = load_settings()

# --- Styles ---
combo_style = """
QLabel {
    color: #ffae42;
    font-size: 14px;
    font-weight: bold;
}
QLabel#CommFieldLabel {
    color: #f1f1f1;
    font-family: 'Etna Sans Serif';
    font-size: 14px;
}
QPushButton {
    background-color: #185dbe;
    color: white;
    border-radius: 10px;
    font-size: 13px;
    min-width: 120px;
    min-height: 36px;
    border: none;
}
QPushButton:hover {
    background-color: #3677ef;
    color: #ffae42;
    border: 1.5px solid #ffae42;
}
QPushButton:pressed {
    background-color: #144799;
    color: #ffefcf;
}
QPushButton#ExitButton {
    background-color: #D32F2F;
    color: white;
    border-radius: 10px;
    font-size: 13px;
    min-width: 120px;
    min-height: 36px;
    border: none;
}
QPushButton#ExitButton:hover {
    background-color: #ff5555;
    color: #232323;
    border: 1.5px solid #fff;
}
QPushButton#ConnectButton[connection="connected"] {
    background-color: #36b37e;
    color: #ffffff;
    border: 2px solid #207245;
}
QPushButton#ConnectButton[connection="disconnected"] {
    background-color: #e74c3c;
    color: #ffffff;
    border: 2px solid #a80000;
}
QComboBox {
    background-color: #232323;
    color: #f1f1f1;
    border: 1.5px solid #bbbbbb;
    border-radius: 5px;
    font-size: 14px;
    min-height: 32px;
    padding-left: 12px;
    padding-right: 24px;
}
QComboBox:hover {
    border: 2px solid #ffae42;
    color: #ffae42;
    background-color: #2e2e2e;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid #444;
    background: #565B5E;
}
QComboBox::down-arrow {
    image: none;
    border: none;
    width: 10px;
    height: 10px;
}
QComboBox QAbstractItemView {
    background-color: #565B5E;
    color: #f1f1f1;
    border: 1px solid #ffffff;
    selection-background-color: #444444;
    border-radius: 5px; 
    selection-color: #ffae42;
    font-size: 14px;
    outline: 0;
}
"""

selected_style = """
QPushButton[selected="true"] {
    background-color: #36b37e;
    color: #ffffff;
    border: 2px solid #207245;
}
"""

def apply_shadow(widget, blur = 16, x_offset = 0, y_offset = 3, color = "#242424"):
    shadow = QGraphicsDropShadowEffect  ()
    shadow.setBlurRadius                (blur)
    shadow.setOffset                    (x_offset, y_offset)
    shadow.setColor                     (QColor(color))
    widget.setGraphicsEffect            (shadow)

class HoverAnimatableButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._anim      = None
        self._base_rect = None
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Enter:
            self._start_lift_animation(up = True)
        elif event.type() == QEvent.Type.Leave:
            self._start_lift_animation(up = False)
            
        return super().eventFilter(obj, event)

    def _start_lift_animation(self, up=True):
        if self._anim and self._anim.state() == QPropertyAnimation.State.Running:
            self._anim.stop()
            
        if self._base_rect is None:
            self._base_rect = self.geometry()
            
        rect = self.geometry()
        
        if up:
            target = QRect(rect.left(), rect.top()-4, rect.width(), rect.height())
        else:
            target = QRect(rect.left(), self._base_rect.top(), rect.width(), rect.height())
            
        self._anim = QPropertyAnimation (self, b"geometry")
        self._anim.setDuration          (110)
        self._anim.setEasingCurve       (QEasingCurve.Type.OutQuad)
        self._anim.setStartValue        (rect)
        self._anim.setEndValue          (target)
        self._anim.start()

class HoverAnimatableCombo(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._anim      = None
        self._base_rect = None
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Enter:
            self._start_lift_animation(up = True)
        elif event.type() == QEvent.Type.Leave:
            self._start_lift_animation(up = False)
            
        return super().eventFilter(obj, event)

    def _start_lift_animation(self, up = True):
        if self._anim and self._anim.state() == QPropertyAnimation.State.Running:
            self._anim.stop()
            
        if self._base_rect is None:
            self._base_rect = self.geometry()
            
        rect = self.geometry()
        
        if up:
            target = QRect(rect.left(), rect.top()-4, rect.width(), rect.height())
        else:
            target = QRect(rect.left(), self._base_rect.top(), rect.width(), rect.height())
            
        self._anim = QPropertyAnimation (self, b"geometry")
        self._anim.setDuration          (110)
        self._anim.setEasingCurve       (QEasingCurve.Type.OutQuad)
        self._anim.setStartValue        (rect)
        self._anim.setEndValue          (target)
        self._anim.start()

def make_button_group(title, button_labels, columns = 2, min_height = 130):
    frame = QFrame()
    frame.setFrameShape(QFrame.Shape.StyledPanel)
    frame.setStyleSheet("""
        QFrame {
            background: #232323;
            border-radius: 14px;
        }
    """)
    frame.setSizePolicy         (QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
    frame.setMinimumHeight      (min_height)
    vlayout = QVBoxLayout       (frame)
    vlayout.setContentsMargins  (12, 12, 12, 12)
    vlayout.setSpacing(7)
    
    if title.strip():
        title_label = QLabel        (title)
        title_label.setStyleSheet   ("color: #ffefcf; font-size: 14px; font-weight: bold;")
        title_label.setAlignment    (Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        vlayout.addWidget           (title_label)
    else:
        vlayout.addSpacing(3)
        
    grid = QGridLayout()
    grid.setHorizontalSpacing(12)
    grid.setVerticalSpacing(12)
    button_refs = []
    
    for idx, label in enumerate(button_labels):
        btn = HoverAnimatableButton(label)
        btn.setMinimumHeight(38)
        
        if label.upper() == "EXIT":
            btn.setObjectName("ExitButton")
            apply_shadow (btn, blur = 24, color = "#a80000")
        elif label.upper() == "CONNECT" or label.upper() == "DISCONNECT":
            btn.setObjectName("ConnectButton")
            apply_shadow(btn, blur = 20, color = "#207245")
        else:
            apply_shadow(btn)
            
        btn.setCursor       (Qt.CursorShape.PointingHandCursor)
        grid.addWidget      (btn, idx // columns, idx % columns)
        button_refs.append  (btn)
        
    vlayout.addLayout(grid)
    return frame, button_refs

def make_system_settings_group(parent, baud_callback, port_callback):
    frame = QFrame()
    frame.setFrameShape(QFrame.Shape.StyledPanel)
    frame.setStyleSheet("""
        QFrame {
            background: #232323;
            border-radius: 14px;
        }
        QLabel#TitleLabel {
            color: #ffefcf;
            font-size: 15px;
            font-weight: bold;
        }
        QLabel#CommFieldLabel {
            color: #f1f1f1;
            font-family: 'Etna Sans Serif';
            font-size: 14px;
        }
        QComboBox {
            background-color: #232323;
            color: #f1f1f1;
            border: 1.5px solid #bbbbbb;
            border-radius: 5px;
            font-size: 14px;
            min-height: 32px;
            padding-left: 12px;
            padding-right: 24px;
        }
        ComboBox:hover {
            border: 2px solid #ffae42;
            color: #ffae42;
            background-color: #2e2e2e;
        }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 24px;
            border-left: 1px solid #444;
            background: #565B5E;
        }
        QComboBox::down-arrow {
            image: none;
            border: none;
            width: 10px;
            height: 10px;
        }
        QComboBox QAbstractItemView {
            background-color: #565B5E;
            color: #f1f1f1;
            border: 1px solid #ffffff;
            border-radius: 5px; 
            selection-background-color: #444444;
            selection-color: #ffae42;
            font-size: 14px;
            outline: 0;
        }
    """)
    
    frame.setSizePolicy                     (QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
    frame.setMinimumHeight                  (130)
    
    vlayout = QVBoxLayout                   (frame)
    vlayout.setContentsMargins              (14, 12, 14, 12)
    vlayout.setSpacing                      (7)
    
    title_label = QLabel                    ("COMMUNICATION AND\nSYSTEM SETTINGS")
    title_label.setObjectName               ("TitleLabel")
    title_label.setAlignment                (Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
    
    vlayout.addWidget                       (title_label)
    grid = QGridLayout                      ()
    grid.setHorizontalSpacing               (24)
    grid.setVerticalSpacing                 (12)
    
    btn_connect = HoverAnimatableButton     ("DISCONNECTED")
    btn_connect.setObjectName               ("ConnectButton")
    btn_connect.setProperty                 ("connection", "disconnected")
    apply_shadow                            (btn_connect, blur = 20, color = "#207245")
    btn_connect.setMinimumHeight            (38)
    btn_connect.setCursor                   (Qt.CursorShape.PointingHandCursor)
    grid.addWidget                          (btn_connect, 0, 0)
    btn_settings = HoverAnimatableButton    ("SYSTEM SETTINGS")
    btn_settings.setMinimumHeight           (38)
    apply_shadow                            (btn_settings)
    btn_settings.setCursor                  (Qt.CursorShape.PointingHandCursor)
    grid.addWidget                          (btn_settings, 1, 0)
    
    port_label = QLabel                     ("COM Port:")
    port_label.setObjectName                ("CommFieldLabel")
    port_label.setAlignment                 (Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    port_combo = HoverAnimatableCombo       ()
    port_combo.setEditable                  (False)
    port_combo.setMinimumWidth              (120)
    apply_shadow                            (port_combo, blur = 18, y_offset = 3, color = "#444444")
    grid.addWidget                          (port_label, 0, 1)
    grid.addWidget                          (port_combo, 0, 2)
    port_combo.currentTextChanged.connect   (port_callback)
    
    baud_label = QLabel                     ("Baud Rate:")
    baud_label.setObjectName                ("CommFieldLabel")
    baud_label.setAlignment                 (Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    baud_combo = HoverAnimatableCombo       ()
    baud_combo.addItems([
        "110", "300", "600", "1200", "2400", "4800", "9600", "14400",
        "19200", "38400", "57600", "115200", "128000", "2560000"
    ])
    baud_combo.setEditable                  (False)
    baud_combo.setMinimumWidth              (100)
    apply_shadow                            (baud_combo, blur = 18, y_offset = 3, color = "#444444")
    grid.addWidget                          (baud_label, 1, 1)
    grid.addWidget                          (baud_combo, 1, 2)
    baud_combo.currentTextChanged.connect   (baud_callback)
    vlayout.addLayout                       (grid)
    # Set baud to last used
    baud_combo.setCurrentText               (serial_settings["baud_rate"])
    port_combo._last_ports = []
    
    def update_ports():
        ports = [p.device for p in serial.tools.list_ports.comports()]
        
        if ports != port_combo._last_ports:
            current = port_combo.currentText()
            port_combo.blockSignals(True)
            port_combo.clear()
            port_combo.addItems(ports)
            
            if current in ports:
                port_combo.setCurrentText(current)
                
            port_combo.blockSignals(False)
            port_combo._last_ports = ports
            
    timer = QTimer(frame)
    timer.timeout.connect(update_ports)
    timer.start(1000)
    update_ports()
    
    return frame, btn_connect, btn_settings, baud_combo, port_combo

class ConnectionSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("System Settings")
        
        # Inherit parent stylesheet for color/font match
        if parent is not None:
            self.setStyleSheet(parent.styleSheet())
            
        layout          = QVBoxLayout(self)
        self._settings  = serial_settings

        # Data Bits
        hlayout = QHBoxLayout                   ()
        label   = QLabel                        ("Data Bits:")
        label.setObjectName                     ("CommFieldLabel")
        hlayout.addWidget                       (label)
        self.data_bits = HoverAnimatableCombo   ()
        self.data_bits.addItems                 (["5", "6", "7", "8"])
        self.data_bits.setCurrentText           (self._settings["data_bits"])
        hlayout.addWidget                       (self.data_bits)
        layout.addLayout                        (hlayout)

        # Parity
        hlayout = QHBoxLayout                   ()
        label = QLabel                          ("Parity:")
        label.setObjectName                     ("CommFieldLabel")
        hlayout.addWidget                       (label)
        self.parity = HoverAnimatableCombo      ()
        self.parity.addItems                    (["None", "Even", "Odd", "Mark", "Space"])
        self.parity.setCurrentText              (self._settings["parity"])
        hlayout.addWidget                       (self.parity)
        layout.addLayout                        (hlayout)

        # Stop Bits
        hlayout = QHBoxLayout                   ()
        label = QLabel                          ("Stop Bits:")
        label.setObjectName                     ("CommFieldLabel")
        hlayout.addWidget                       (label)
        self.stop_bits = HoverAnimatableCombo   ()
        self.stop_bits.addItems                 (["1", "1.5", "2"])
        self.stop_bits.setCurrentText           (self._settings["stop_bits"])
        hlayout.addWidget                       (self.stop_bits)
        layout.addLayout                        (hlayout)

        # Flow Control
        hlayout = QHBoxLayout                   ()
        label   = QLabel                        ("Flow Control:")
        label.setObjectName                     ("CommFieldLabel")
        hlayout.addWidget                       (label)
        self.flow_control = HoverAnimatableCombo()
        self.flow_control.addItems              (["None", "RTS/CTS", "XON/XOFF"])
        self.flow_control.setCurrentText        (self._settings["flow_control"])
        hlayout.addWidget                       (self.flow_control)
        layout.addLayout                        (hlayout)

        # Send Setting
        hlayout = QHBoxLayout                   ()
        label   = QLabel                        ("Send As:")
        label.setObjectName                     ("CommFieldLabel")
        hlayout.addWidget                       (label)
        self.send_as = HoverAnimatableCombo     ()
        self.send_as.addItems                   (["Text", "Hex"])
        self.send_as.setCurrentText             (self._settings["send_as"])
        hlayout.addWidget                       (self.send_as)
        layout.addLayout                        (hlayout)

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)

    def accept(self):
        # Save all values back to the settings
        serial_settings["data_bits"]    = self.data_bits.currentText()
        serial_settings["parity"]       = self.parity.currentText()
        serial_settings["stop_bits"]    = self.stop_bits.currentText()
        serial_settings["flow_control"] = self.flow_control.currentText()
        serial_settings["send_as"]      = self.send_as.currentText()
        save_settings(serial_settings)
        super().accept()

class BottomToolbar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QHBoxLayout       (self)
        main_layout.setContentsMargins  (16, 10, 16, 10)
        main_layout.setSpacing          (18)
        
        self.setSizePolicy      (QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight   (170)
        self.setStyleSheet      (combo_style + selected_style)
        
        manual_group, self.manual_buttons = make_button_group(
            "MANUAL MODE\nCONTROL SELECTION",
            ["KEYBOARD CONTROL", "REMOTE CONTROLLER", "AMBOT R-CONTROLLER", "MOBILE APP"],
            columns = 2
        )
        main_layout.addWidget(manual_group)
        
        auto_group, self.auto_buttons = make_button_group(
            "AUTOMATIC MODE\nCONTROL SELECTION",
            ["VOICE MODE", "FULLY AUTONOMOUS", "CHAT MODE", "GPS"],
            columns = 2
        )
        main_layout.addWidget(auto_group)
        
        modes_group, self.mode_buttons = make_button_group(
            "SYSTEM\nCONTROL MODES",
            ["Manual Mode", "Automatic Mode"],
            columns = 1,
            min_height = 105
        )
        main_layout.addWidget(modes_group)
        
        sys_group, self.connect_btn, self.settings_btn, self.baud_combo, self.port_combo = make_system_settings_group(
            self, self.on_baud_rate_changed, self.on_com_port_changed
        )
        main_layout.addWidget(sys_group)
        
        logout_group, self.logout_buttons = make_button_group(
            "",
            ["LOGOUT", "EXIT"],
            columns=1,
            min_height=105
        )
        
        main_layout.addWidget(logout_group)
        self.manual_mode_active     = False
        self.automatic_mode_active  = False
        self.selected_manual_idx    = None
        self.selected_auto_idx      = None
        self.connected              = False
        self.serial_port            = None
        
        self._connect_signals           ()
        self.set_manual_mode            (False)
        self.set_automatic_mode         (False)
        self._set_mode_selected         (True)
        self._set_selected_button       (self.manual_buttons, -1)
        self._set_selected_button       (self.auto_buttons, -1)
        self.baud_combo.setCurrentText  (serial_settings["baud_rate"]) # Set baud combo from last-used
        
        for idx, btn in enumerate(self.manual_buttons):
            btn.clicked.connect(lambda _, i=idx: self.on_manual_control_selected(i))
            
        for idx, btn in enumerate(self.auto_buttons):
            btn.clicked.connect(lambda _, i=idx: self.on_auto_control_selected(i))

    def _connect_signals(self):
        self.mode_buttons[0].clicked.connect    (self.on_manual_mode)
        self.mode_buttons[1].clicked.connect    (self.on_automatic_mode)
        
        self.connect_btn.clicked.connect        (self.on_connect_disconnect)
        self.settings_btn.clicked.connect       (self.show_connection_settings)
        
        self.logout_buttons[0].clicked.connect  (self.on_logout)
        self.logout_buttons[1].clicked.connect  (self.on_exit)

    def set_manual_mode(self, active=True):
        for btn in self.manual_buttons:
            btn.setEnabled(active)
            
        for btn in self.auto_buttons:
            btn.setEnabled(not active)
            
        self.manual_mode_active     = active
        self.automatic_mode_active  = not active

    def set_automatic_mode(self, active=True):
        for btn in self.auto_buttons:
            btn.setEnabled(active)
            
        for btn in self.manual_buttons:
            btn.setEnabled(not active)
            
        self.automatic_mode_active  = active
        self.manual_mode_active     = not active

    def _set_mode_selected(self, manual_selected: bool):
        self.mode_buttons[0].setProperty        ("selected", manual_selected)
        self.mode_buttons[1].setProperty        ("selected", not manual_selected)
        self.mode_buttons[0].style().unpolish   (self.mode_buttons[0])
        self.mode_buttons[0].style().polish     (self.mode_buttons[0])
        self.mode_buttons[1].style().unpolish   (self.mode_buttons[1])
        self.mode_buttons[1].style().polish     (self.mode_buttons[1])

    def _set_selected_button(self, buttons, selected_idx):
        for idx, btn in enumerate(buttons):
            btn.setProperty("selected", idx == selected_idx)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def on_manual_control_selected(self, idx):
        self.selected_manual_idx = idx
        self._set_selected_button(self.manual_buttons, idx)
        print(f"Manual Control Selected: {self.manual_buttons[idx].text()}")

    def on_auto_control_selected(self, idx):
        self.selected_auto_idx = idx
        self._set_selected_button(self.auto_buttons, idx)
        print(f"Automatic Control Selected: {self.auto_buttons[idx].text()}")

    def on_manual_mode(self):
        print("Manual Mode pressed")
        self.set_manual_mode(True)
        self.set_automatic_mode(False)
        self._set_mode_selected(True)
        self.selected_auto_idx = None
        self._set_selected_button(self.auto_buttons, -1)
        self.selected_manual_idx = None
        self._set_selected_button(self.manual_buttons, -1)

    def on_automatic_mode(self):
        print("Automatic Mode pressed")
        self.set_manual_mode(False)
        self.set_automatic_mode(True)
        self._set_mode_selected(False)
        self.selected_manual_idx = None
        self._set_selected_button(self.manual_buttons, -1)
        self.selected_auto_idx = None
        self._set_selected_button(self.auto_buttons, -1)

    def on_connect_disconnect(self):
        # Always use the current baud from settings
        serial_settings["baud_rate"] = self.baud_combo.currentText()
        save_settings(serial_settings)
        
        if not self.connected:
            port_name   = self.port_combo.currentText()
            baudrate    = int(serial_settings["baud_rate"])
            
            if not port_name:
                parent_window = self.window()
                Dialouge_Boxes.No_COMPORT_Selected(parent_window)
                
                return
            try:
                self.serial_port = serial.Serial(
                    port = port_name,
                    baudrate=baudrate,
                    bytesize = int(serial_settings["data_bits"]),
                    parity = serial.PARITY_NONE if serial_settings["parity"] == "None" else {
                        "Even": serial.PARITY_EVEN,
                        "Odd": serial.PARITY_ODD,
                        "Mark": serial.PARITY_MARK,
                        "Space": serial.PARITY_SPACE
                    }[serial_settings["parity"]],
                    stopbits    = float(serial_settings["stop_bits"]),
                    timeout     = 1,
                    xonxoff     = (serial_settings["flow_control"] == "XON/XOFF"),
                    rtscts      = (serial_settings["flow_control"] == "RTS/CTS")
                )
                self.connected = True
                self.connect_btn.setText("CONNECTED")
                self.connect_btn.setProperty("connection", "connected")
                
            except Exception as e:
                self.connected = False
                self.connect_btn.setText("DISCONNECTED")
                self.connect_btn.setProperty("connection", "disconnected")
                parent_window = self.window()
                Dialouge_Boxes.Connection_Disconnected(parent_window, e)
                
        else:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
                
            self.connected = False
            self.connect_btn.setText("DISCONNECTED")
            self.connect_btn.setProperty("connection", "disconnected")
            
        self.connect_btn.style().unpolish(self.connect_btn)
        self.connect_btn.style().polish(self.connect_btn)
        print(f"Connection state: {'Connected' if self.connected else 'Disconnected'}")

    def on_baud_rate_changed(self, baud):
        serial_settings["baud_rate"] = baud
        save_settings(serial_settings)
        print(f"Selected baud rate: {baud}")
        self.baud_rate = baud

    def on_com_port_changed(self, port):
        print(f"Selected COM port: {port}")
        self.com_port = port

    def show_connection_settings(self):
        dlg = ConnectionSettingsDialog(self)
        if dlg.exec():
            # Apply changes if needed (already saved)
            print("Settings changed.")

    def on_logout(self): print("LOGOUT pressed")
    def on_exit(self):
        parent_window = self.window()
        if Dialouge_Boxes.request_exit(parent_window):
            parent_window.close()
