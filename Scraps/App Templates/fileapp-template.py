# -*- coding: utf-8 -*-
"""
Created on Sat Jun 8 3:37:43 2024

@author: Thomas
"""




import tkinter as tk
from tkinter import ttk
import json

class FileApp:
    def __init__(self, root, settings_path):
        self.root = root
        self.root.title("FileApp")
        self.settings_path = settings_path
        self.load_settings()
        self.create_widgets()
        
    def create_widgets(self):
        menubar = tk.Menu(self.root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open", command=self.open_file)
        filemenu.add_command(label="Save", command=self.save_file)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        
        optionsmenu = tk.Menu(menubar, tearoff=0)
        optionsmenu.add_checkbutton(label="Stay on Top", command=self.toggle_stay_on_top)
        optionsmenu.add_checkbutton(label="Minimize to Tray", command=self.toggle_min_to_tray)
        optionsmenu.add_checkbutton(label="Dark Mode", command=self.toggle_dark_mode)
        menubar.add_cascade(label="Options", menu=optionsmenu)
        
        self.root.config(menu=menubar)
        
        self.text = tk.Text(self.root)
        self.text.pack(expand=True, fill=tk.BOTH)
        
        self.button = ttk.Button(self.root, text="Click Me", command=self.button_click)
        self.button.pack(pady=10)
        
    def load_settings(self):
        try:
            with open(self.settings_path, 'r') as f:
                self.settings = json.load(f)
        except FileNotFoundError:
            self.settings = {}
        
    def save_settings(self):
        with open(self.settings_path, 'w') as f:
            json.dump(self.settings, f)
    
    def open_file(self):
        # Open file logic
        pass
    
    def save_file(self):
        # Save file logic
        pass
    
    def button_click(self):
        # Button click logic
        pass
    
    def toggle_stay_on_top(self):
        self.root.wm_attributes("-topmost", not self.root.attributes("-topmost"))
    
    def toggle_min_to_tray(self):
        # Minimize to tray logic
        pass
    
    def toggle_dark_mode(self):
        # Dark mode logic
        pass
    
    def set_tray_app(self, tray_app):
        self.tray_app = tray_app
