# -*- coding: utf-8 -*-
"""
Created on Sat Jun 8 3:39:05 2024

@author: Thomas
"""



import threading
import tkinter as tk
from pystray import Icon, MenuItem as item, Menu
from PIL import Image, ImageDraw

class TrayApp:
    def __init__(self, file_app, settings_path, icon_image):
        self.file_app = file_app
        self.settings_path = settings_path
        self.icon_image = icon_image
        self.create_tray_icon()
        
    def create_tray_icon(self):
        menu = Menu(item('Show', self.show_window), item('Exit', self.exit_app))
        self.tray_icon = Icon("AppTray", self.icon_image, "AppTray", menu)
        self.tray_icon.run_detached()
    
    def show_window(self, icon, item):
        self.file_app.root.deiconify()
        self.file_app.root.lift()
    
    def exit_app(self, icon, item):
        self.file_app.save_settings()
        icon.stop()
        self.file_app.root.quit()
