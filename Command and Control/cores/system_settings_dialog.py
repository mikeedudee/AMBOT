import os
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QColorDialog, QFileDialog, QFontComboBox, QSpinBox, QMessageBox, QCheckBox, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont, QColor

# ----------------------------- Settings Manager (Singleton) -----------------------------
class SettingsManager:
    SETTINGS_FILE = os.path.expanduser("~/.my_serial_settings.json")
    DEFAULTS = {
        "version": "1.2.4",
        "organization": "AMBOT",
        "logo_path": "",
        "language": "en",
        "theme": "Dark",
        "accent_color": "#36b37e",
        "font_family": "Etna Sans Serif",
        "font_size": 14,
        "high_contrast": False,
        "communication": {
            "baud_rate": "9600",
            "data_bits": "8",
            "parity": "None",
            "stop_bits": "1",
            "flow_control": "None",
            "send_as": "Text",
            "profile": "Default",
            "profiles": {
                "Default": {
                    "baud_rate": "9600",
                    "data_bits": "8",
                    "parity": "None",
                    "stop_bits": "1",
                    "flow_control": "None",
                    "send_as": "Text"
                }
            }
        }
    }
    SUPPORTED_LANGUAGES = {
        'en': "English",
        'fil': "Filipino"
    }
    # Localized strings (expandable)
    TRANSLATIONS = {
        "en": {
            "Communication": "Communication",
            "Appearance": "Appearance",
            "Accessibility": "Accessibility",
            "Profiles": "Profiles",
            "About": "About",
            "Port": "Port",
            "Baud Rate": "Baud Rate",
            "Data Bits": "Data Bits",
            "Parity": "Parity",
            "Stop Bits": "Stop Bits",
            "Flow Control": "Flow Control",
            "Send As": "Send As",
            "Profile": "Profile",
            "Save Profile": "Save Profile",
            "Load Profile": "Load Profile",
            "Delete Profile": "Delete Profile",
            "Theme": "Theme",
            "Font": "Font",
            "Font Size": "Font Size",
            "Accent Color": "Accent Color",
            "High Contrast": "High Contrast",
            "Keyboard Shortcuts": "Keyboard Shortcuts",
            "Restore Defaults": "Restore Defaults",
            "Export Settings": "Export Settings",
            "Import Settings": "Import Settings",
            "Select Logo": "Select Logo",
            "Organization": "Organization",
            "Version": "Version",
            "Error Log": "Error Log",
            "Language": "Language",
            "OK": "OK",
            "Cancel": "Cancel",
            "Apply": "Apply",
            "Factory Reset?": "Are you sure you want to restore factory defaults?",
            "YES": "Yes",
            "NO": "No"
        },
        "fil": {
            "Communication": "Komunikasyon",
            "Appearance": "Itsura",
            "Accessibility": "Accessibility",
            "Profiles": "Mga Profile",
            "About": "Tungkol",
            "Port": "Port",
            "Baud Rate": "Baud Rate",
            "Data Bits": "Data Bits",
            "Parity": "Parity",
            "Stop Bits": "Stop Bits",
            "Flow Control": "Flow Control",
            "Send As": "Ipadala Bilang",
            "Profile": "Profile",
            "Save Profile": "I-save ang Profile",
            "Load Profile": "I-load ang Profile",
            "Delete Profile": "Tanggalin ang Profile",
            "Theme": "Tema",
            "Font": "Font",
            "Font Size": "Laki ng Font",
            "Accent Color": "Accent na Kulay",
            "High Contrast": "Mataas na Contrast",
            "Keyboard Shortcuts": "Mga Shortcut sa Keyboard",
            "Restore Defaults": "Ibalik sa Default",
            "Export Settings": "I-export ang Settings",
            "Import Settings": "I-import ang Settings",
            "Select Logo": "Piliin ang Logo",
            "Organization": "Organisasyon",
            "Version": "Bersyon",
            "Error Log": "Log ng Error",
            "Language": "Wika",
            "OK": "OK",
            "Cancel": "Kanselahin",
            "Apply": "Ilapat",
            "Factory Reset?": "Sigurado ka bang ibabalik sa factory default?",
            "YES": "Oo",
            "NO": "Hindi"
        }
    }
    def __init__(self):
        self.settings = self.DEFAULTS.copy()
        self.load()
        self.language = self.settings.get("language", "en")
    def translate(self, key):
        return self.TRANSLATIONS[self.language].get(key, key)
    def set_language(self, lang):
        if lang in self.SUPPORTED_LANGUAGES:
            self.language = lang
            self.settings["language"] = lang
            self.save()
    def load(self):
        if os.path.exists(self.SETTINGS_FILE):
            try:
                with open(self.SETTINGS_FILE, "r") as f:
                    self.settings = json.load(f)
            except Exception:
                self.settings = self.DEFAULTS.copy()
    def save(self):
        try:
            with open(self.SETTINGS_FILE, "w") as f:
                json.dump(self.settings, f, indent=2)
        except Exception:
            pass
    def factory_reset(self):
        self.settings = self.DEFAULTS.copy()
        self.save()
    def export_settings(self, filepath):
        try:
            with open(filepath, "w") as f:
                json.dump(self.settings, f, indent=2)
        except Exception:
            pass
    def import_settings(self, filepath):
        try:
            with open(filepath, "r") as f:
                self.settings = json.load(f)
            self.save()
        except Exception:
            pass

settings_manager = SettingsManager()

# ----------------------------- System Settings Dialog -----------------------------
class SystemSettingsDialog(QDialog):
    # Signal for live update
    settings_changed = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("System Settings")
        self.setMinimumSize(540, 440)
        self.setModal(True)
        self.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab { font-size:15px; min-width:130px; padding:10px; }
            QLabel { font-size: 14px; }
        """)
        self.manager = settings_manager
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_communication(), self.manager.translate("Communication"))
        self.tabs.addTab(self._tab_appearance(),    self.manager.translate("Appearance"))
        self.tabs.addTab(self._tab_accessibility(), self.manager.translate("Accessibility"))
        self.tabs.addTab(self._tab_profiles(),      self.manager.translate("Profiles"))
        self.tabs.addTab(self._tab_about(),         self.manager.translate("About"))
        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)
        # OK, Cancel, Apply
        btns = QHBoxLayout()
        self.ok_btn = QPushButton(self.manager.translate("OK"))
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton(self.manager.translate("Cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        self.apply_btn = QPushButton(self.manager.translate("Apply"))
        self.apply_btn.clicked.connect(self.apply)
        btns.addWidget(self.ok_btn)
        btns.addWidget(self.cancel_btn)
        btns.addWidget(self.apply_btn)
        layout.addLayout(btns)
        self.apply_btn.setDefault(True)
        self.apply_btn.setAutoDefault(True)
    # --- Communication Tab
    def _tab_communication(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        comm = self.manager.settings["communication"]
        # Profile selection
        prof_layout = QHBoxLayout()
        prof_layout.addWidget(QLabel(self.manager.translate("Profile") + ":"))
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(comm["profiles"].keys())
        self.profile_combo.setCurrentText(comm.get("profile", "Default"))
        prof_layout.addWidget(self.profile_combo)
        btn_save_prof = QPushButton(self.manager.translate("Save Profile"))
        btn_save_prof.clicked.connect(self.save_profile)
        btn_del_prof = QPushButton(self.manager.translate("Delete Profile"))
        btn_del_prof.clicked.connect(self.delete_profile)
        prof_layout.addWidget(btn_save_prof)
        prof_layout.addWidget(btn_del_prof)
        layout.addLayout(prof_layout)
        # Main fields
        grid = QHBoxLayout()
        form = QVBoxLayout()
        # Baud Rate
        lbl_baud = QLabel(self.manager.translate("Baud Rate") + ":")
        self.baud_combo = QComboBox()
        self.baud_combo.addItems([
            "110", "300", "600", "1200", "2400", "4800", "9600", "14400",
            "19200", "38400", "57600", "115200", "128000", "2560000"
        ])
        self.baud_combo.setCurrentText(comm.get("baud_rate", "9600"))
        form.addWidget(lbl_baud)
        form.addWidget(self.baud_combo)
        # Data Bits
        lbl_db = QLabel(self.manager.translate("Data Bits") + ":")
        self.data_bits_combo = QComboBox()
        self.data_bits_combo.addItems(["5", "6", "7", "8"])
        self.data_bits_combo.setCurrentText(comm.get("data_bits", "8"))
        form.addWidget(lbl_db)
        form.addWidget(self.data_bits_combo)
        # Parity
        lbl_parity = QLabel(self.manager.translate("Parity") + ":")
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["None", "Even", "Odd", "Mark", "Space"])
        self.parity_combo.setCurrentText(comm.get("parity", "None"))
        form.addWidget(lbl_parity)
        form.addWidget(self.parity_combo)
        # Stop Bits
        lbl_sb = QLabel(self.manager.translate("Stop Bits") + ":")
        self.stop_bits_combo = QComboBox()
        self.stop_bits_combo.addItems(["1", "1.5", "2"])
        self.stop_bits_combo.setCurrentText(comm.get("stop_bits", "1"))
        form.addWidget(lbl_sb)
        form.addWidget(self.stop_bits_combo)
        # Flow Control
        lbl_fc = QLabel(self.manager.translate("Flow Control") + ":")
        self.flow_combo = QComboBox()
        self.flow_combo.addItems(["None", "RTS/CTS", "XON/XOFF"])
        self.flow_combo.setCurrentText(comm.get("flow_control", "None"))
        form.addWidget(lbl_fc)
        form.addWidget(self.flow_combo)
        # Send As
        lbl_send = QLabel(self.manager.translate("Send As") + ":")
        self.send_as_combo = QComboBox()
        self.send_as_combo.addItems(["Text", "Hex"])
        self.send_as_combo.setCurrentText(comm.get("send_as", "Text"))
        form.addWidget(lbl_send)
        form.addWidget(self.send_as_combo)
        grid.addLayout(form)
        layout.addLayout(grid)
        return page
    # --- Appearance Tab
    def _tab_appearance(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        # Theme
        theme_layout = QHBoxLayout()
        lbl_theme = QLabel(self.manager.translate("Theme") + ":")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "System"])
        self.theme_combo.setCurrentText(self.manager.settings.get("theme", "Dark"))
        theme_layout.addWidget(lbl_theme)
        theme_layout.addWidget(self.theme_combo)
        layout.addLayout(theme_layout)
        # Font family
        font_layout = QHBoxLayout()
        lbl_font = QLabel(self.manager.translate("Font") + ":")
        self.font_combo = QFontComboBox()
        try:
            self.font_combo.setCurrentFont(QFont(self.manager.settings.get("font_family", "Etna Sans Serif")))
        except Exception:
            pass
        font_layout.addWidget(lbl_font)
        font_layout.addWidget(self.font_combo)
        layout.addLayout(font_layout)
        # Font size
        size_layout = QHBoxLayout()
        lbl_size = QLabel(self.manager.translate("Font Size") + ":")
        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 64)
        self.size_spin.setValue(int(self.manager.settings.get("font_size", 14)))
        size_layout.addWidget(lbl_size)
        size_layout.addWidget(self.size_spin)
        layout.addLayout(size_layout)
        # Accent color
        accent_layout = QHBoxLayout()
        lbl_accent = QLabel(self.manager.translate("Accent Color") + ":")
        self.accent_btn = QPushButton(self.manager.settings.get("accent_color", "#36b37e"))
        self.accent_btn.clicked.connect(self.pick_accent)
        accent_layout.addWidget(lbl_accent)
        accent_layout.addWidget(self.accent_btn)
        layout.addLayout(accent_layout)
        # Reset
        reset_btn = QPushButton(self.manager.translate("Restore Defaults"))
        reset_btn.clicked.connect(self.restore_defaults)
        layout.addWidget(reset_btn)
        return page
    # --- Accessibility Tab
    def _tab_accessibility(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        # High contrast
        self.contrast_box = QCheckBox(self.manager.translate("High Contrast"))
        self.contrast_box.setChecked(self.manager.settings.get("high_contrast", False))
        layout.addWidget(self.contrast_box)
        # Keyboard shortcuts info
        layout.addWidget(QLabel(self.manager.translate("Keyboard Shortcuts") + ":"))
        shortcuts = QLabel("<b>Ctrl+S</b>: Save, <b>Ctrl+Q</b>: Quit, <b>F1</b>: Help, ...")
        layout.addWidget(shortcuts)
        return page
    # --- Profiles Tab
    def _tab_profiles(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        # Export/Import
        h = QHBoxLayout()
        export_btn = QPushButton(self.manager.translate("Export Settings"))
        export_btn.clicked.connect(self.export_settings)
        import_btn = QPushButton(self.manager.translate("Import Settings"))
        import_btn.clicked.connect(self.import_settings)
        h.addWidget(export_btn)
        h.addWidget(import_btn)
        layout.addLayout(h)
        # Factory reset
        reset_btn = QPushButton(self.manager.translate("Restore Defaults"))
        reset_btn.clicked.connect(self.restore_defaults)
        layout.addWidget(reset_btn)
        return page
    # --- About Tab
    def _tab_about(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        # Logo
        logo_layout = QHBoxLayout()
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(64,64)
        self.logo_path = self.manager.settings.get("logo_path","")
        if self.logo_path and os.path.exists(self.logo_path):
            self.logo_label.setPixmap(QPixmap(self.logo_path).scaled(64,64, Qt.AspectRatioMode.KeepAspectRatio))
        logo_layout.addWidget(self.logo_label)
        select_logo_btn = QPushButton(self.manager.translate("Select Logo"))
        select_logo_btn.clicked.connect(self.select_logo)
        logo_layout.addWidget(select_logo_btn)
        layout.addLayout(logo_layout)
        # Org & Version
        layout.addWidget(QLabel(f"{self.manager.translate('Organization')}: {self.manager.settings.get('organization','AMBOT')}"))
        layout.addWidget(QLabel(f"{self.manager.translate('Version')}: {self.manager.settings.get('version','1.2.4')}"))
        # Error log (simple)
        layout.addWidget(QLabel(self.manager.translate("Error Log")+":"))
        self.err_log = QTextEdit()
        self.err_log.setReadOnly(True)
        self.err_log.setPlainText("No errors.") # Placeholder
        layout.addWidget(self.err_log)
        return page
    # ---- Button handlers ----
    def pick_accent(self):
        color = QColorDialog.getColor(QColor(self.accent_btn.text()), self, "Accent Color")
        if color.isValid():
            self.accent_btn.setText(color.name())
            self.accent_btn.setStyleSheet(f"background:{color.name()}")
    def save_profile(self):
        name, ok = QInputDialog.getText(self, "Profile Name", "Enter new profile name:")
        if ok and name:
            comm = self.manager.settings["communication"]
            comm["profiles"][name] = {
                "baud_rate": self.baud_combo.currentText(),
                "data_bits": self.data_bits_combo.currentText(),
                "parity": self.parity_combo.currentText(),
                "stop_bits": self.stop_bits_combo.currentText(),
                "flow_control": self.flow_combo.currentText(),
                "send_as": self.send_as_combo.currentText()
            }
            self.profile_combo.addItem(name)
            self.profile_combo.setCurrentText(name)
            comm["profile"] = name
    def delete_profile(self):
        name = self.profile_combo.currentText()
        if name != "Default":
            comm = self.manager.settings["communication"]
            comm["profiles"].pop(name, None)
            self.profile_combo.removeItem(self.profile_combo.currentIndex())
            self.profile_combo.setCurrentText("Default")
            comm["profile"] = "Default"
    def export_settings(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Settings", "", "JSON Files (*.json)")
        if path:
            self.manager.export_settings(path)
            QMessageBox.information(self, "Exported", "Settings exported.")
    def import_settings(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Settings", "", "JSON Files (*.json)")
        if path:
            self.manager.import_settings(path)
            QMessageBox.information(self, "Imported", "Settings imported. Please restart app.")
    def restore_defaults(self):
        reply = QMessageBox.question(
            self, "Restore Defaults",
            self.manager.translate("Factory Reset?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.manager.factory_reset()
            QMessageBox.information(self, "Reset", "Defaults restored. Please restart app.")
            self.close()
    def select_logo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Logo", "", "Image Files (*.png *.jpg *.bmp)")
        if path:
            self.manager.settings["logo_path"] = path
            self.manager.save()
            self.logo_label.setPixmap(QPixmap(path).scaled(64,64, Qt.AspectRatioMode.KeepAspectRatio))
    def apply(self):
        # Communication
        comm = self.manager.settings["communication"]
        comm["baud_rate"] = self.baud_combo.currentText()
        comm["data_bits"] = self.data_bits_combo.currentText()
        comm["parity"] = self.parity_combo.currentText()
        comm["stop_bits"] = self.stop_bits_combo.currentText()
        comm["flow_control"] = self.flow_combo.currentText()
        comm["send_as"] = self.send_as_combo.currentText()
        comm["profile"] = self.profile_combo.currentText()
        # Appearance
        self.manager.settings["theme"] = self.theme_combo.currentText()
        self.manager.settings["font_family"] = self.font_combo.currentFont().family()
        self.manager.settings["font_size"] = self.size_spin.value()
        self.manager.settings["accent_color"] = self.accent_btn.text()
        # Accessibility
        self.manager.settings["high_contrast"] = self.contrast_box.isChecked()
        self.manager.save()
        self.settings_changed.emit()
    def accept(self):
        self.apply()
        super().accept()
