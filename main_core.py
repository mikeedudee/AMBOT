import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import customtkinter as ctk
import cupy as cp
from stl import mesh

ASSETS_PATH = Path(__file__).resolve().parent / "assets"

class TelemetryDashboard:
    def __init__(self):
        self.main_window = ctk.CTk()
        
        ctk.set_appearance_mode                 ("dark")
        ctk.set_default_color_theme             ("dark-blue")  # Use your custom theme
        
        self.main_window.title                  ("AMBOT Telemetry Dashboard")
        self.main_window.attributes             ("-fullscreen", True)
        
        self.main_window.iconbitmap             (ASSETS_PATH / 'AMBOT_main_icon.ico')
        
        self.main_window.grid_columnconfigure   (0, weight = 1)
        self.main_window.grid_rowconfigure      (1, weight = 1)

        self.main_window.bind                   ("<Escape>",    self.exit_app)
        self.main_window.bind                   ("<F11>",       self.exit_fullscreen)

    def run(self):
        self.main_window.mainloop()
        
    def exit_app(self, event = None) -> None:
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.main_window.destroy()
            
    def exit_fullscreen(self, event=None):
        self.main_window.attributes("-fullscreen", False)
        
if __name__ == "__main__":
    telemetry_dashboard = TelemetryDashboard()
    telemetry_dashboard.run()