# -*- coding: utf-8 -*-
"""
Created on Sat Jun 8 3:35:53 2024

@author: Thomas
"""


import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw
from FileApp import FileApp
from TrayApp import TrayApp

def create_icon():
    image = Image.new('RGB', (64, 64), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 63, 63), outline=(0, 0, 0))
    return image

def main():
    root = tk.Tk()
    app_directory = os.path.dirname(os.path.abspath(__file__))
    settings_path = os.path.join(app_directory, 'settings.json')
    
    file_app = FileApp(root, settings_path)
    icon_image = create_icon()
    tray_app = TrayApp(file_app, settings_path, icon_image)
    file_app.set_tray_app(tray_app)
    
    root.mainloop()

if __name__ == "__main__":
    main()
