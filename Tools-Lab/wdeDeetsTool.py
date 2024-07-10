# -*- coding: utf-8 -*-
"""
Created on Tue Jul 9 13:40:21 2024

@author: Thomas
"""



# -*- coding: utf-8 -*-
"""
WDEDetectTool.py

This module provides a graphical user interface for detecting and visualizing
Windows Desktop Environment details, including monitor and taskbar information.

Classes:
- WDEDetectTool: Main GUI application for detecting and visualizing desktop environment details.

Functions:
- detect_wde_deets(): Detects Windows desktop environment details.
- view_wde_map(desktop_info, show_legend=True, show_details=False): Generates a visual map of the desktop environment.
- generate_mini_map(desktop_info, mouse_x, mouse_y): Generates a mini-map with current mouse position.

Usage:
    To run as a standalone application:
    python WDEDetectTool.py

    To use the detection and map generation functions in another script:
    from WDEDetectTool import detect_wde_deets, view_wde_map, generate_mini_map

    desktop_info = detect_wde_deets()
    map_image = view_wde_map(desktop_info)
    mini_map = generate_mini_map(desktop_info, mouse_x, mouse_y)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
from datetime import datetime
from monitorinfoexhelper import get_monitors_info
from wde_map_generator import generate_map, show_mouse_position
from PIL import ImageTk, Image
import pyautogui

class wdeDeetsTool(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Windows Desktop Environment Details Detection Tool")
        self.geometry("400x600")
        
        self.output_text = tk.Text(self, wrap=tk.WORD)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.detect_button = ttk.Button(self, text="Detect Details", command=self.detect_wde_deets)
        self.detect_button.pack(pady=5)
        
        self.save_deets_button = ttk.Button(self, text="Save Details", command=self.save_deets, state=tk.DISABLED)
        self.save_deets_button.pack(pady=5)
        
        self.map_button = ttk.Button(self, text="Show Map", command=self.show_map, state=tk.DISABLED)
        self.map_button.pack(pady=5)
        
        self.mini_map_button = ttk.Button(self, text="Show Mini-Map", command=self.show_mini_map, state=tk.DISABLED)
        self.mini_map_button.pack(pady=5)

        self.save_map_button = ttk.Button(self, text="Save Map", width=14, command=self.save_map, state=tk.DISABLED)
        self.save_map_button.pack(pady=(0, 10))

        self.desktop_info = None
        self.mini_map_window = None

    def detect_wde_deets(self):
        """Detects the Windows desktop environment details."""
        self.desktop_info = {"monitors": get_monitors_info()}
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, json.dumps(self.desktop_info, indent=4))
        
        self.save_deets_button.config(state=tk.NORMAL)
        self.map_button.config(state=tk.NORMAL)
        self.mini_map_button.config(state=tk.NORMAL)

    def save_deets(self):
        """Saves the detected desktop environment details to a JSON file."""
        if not self.desktop_info:
            messagebox.showwarning("No Data", "Please detect details first.")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"desktop_info_{timestamp}.json"
        
        file_path = filedialog.asksaveasfilename(defaultextension=".json", initialfile=default_filename)
        if file_path:
            with open(file_path, 'w') as file:
                json.dump(self.desktop_info, file, indent=4)
            messagebox.showinfo("Saved", f"Desktop info saved to {file_path}")

    def show_map(self):
        """Generates and displays the desktop environment map."""
        if not self.desktop_info:
            messagebox.showwarning("No Data", "Please detect details first.")
            return

        options = {
            "show_grid": messagebox.askyesno("Map Options", "Show grid?"),
            "show_numbers": messagebox.askyesno("Map Options", "Show coordinate numbers?"),
            "show_legend": messagebox.askyesno("Map Options", "Show legend?"),
            "show_details": messagebox.askyesno("Map Options", "Show detailed information?")
        }

        map_image = generate_map(self.desktop_info, **options)
        map_image.show()
        self.save_map_button.config(state=tk.NORMAL)

    def show_mini_map(self):
        """Displays a mini-map with real-time mouse position updates."""
        if not self.desktop_info:
            messagebox.showwarning("No Data", "Please detect details first.")
            return

        if self.mini_map_window:
            self.mini_map_window.destroy()

        self.mini_map_window = tk.Toplevel(self)
        self.mini_map_window.title("Desktop Mini-Map")
        self.mini_map_window.geometry("800x800")

        mini_map_label = tk.Label(self.mini_map_window)
        mini_map_label.pack(expand=True, fill=tk.BOTH)

        base_map = generate_map(self.desktop_info, show_grid=True, show_numbers=True)

        def update_mini_map(Image):
            if self.mini_map_window.winfo_exists():
                mouse_x, mouse_y = pyautogui.position()
                mini_map = show_mouse_position(base_map.copy(), mouse_x, mouse_y)
                mini_map.thumbnail((800, 800), Image.LANCZOS)
                
                mini_map_tk = ImageTk.PhotoImage(mini_map)
                mini_map_label.config(image=mini_map_tk)
                mini_map_label.image = mini_map_tk
                self.mini_map_window.after(100, lambda: update_mini_map(Image))

        update_mini_map(Image)


    def save_map(self):
        if not hasattr(self, 'map_image'):
            messagebox.showwarning("No Map", "Please generate the map first.")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"desktop_map_{timestamp}.png"
        
        file_path = filedialog.asksaveasfilename(defaultextension=".png", initialfile=default_filename)
        if file_path:
            self.map_image.save(file_path)
            messagebox.showinfo("Saved", f"Desktop map saved to {file_path}")
        self.save_map_button.config(state=tk.DISABLED)

if __name__ == "__main__":
    app = wdeDeetsTool()
    app.mainloop()






# # wdedetecttool.py

# import tkinter as tk
# from tkinter import ttk, filedialog, messagebox
# import json
# from datetime import datetime
# from screeninfo import get_monitors
# from appbarhelper import get_taskbar_info
# from PIL import Image, ImageDraw

# class WDEDetectTool(tk.Tk):
#     def __init__(self):
#         super().__init__()
#         self.title("Windows Desktop Environment Details Detection Tool")
#         self.geometry("400x600")
        
#         self.output_text = tk.Text(self, wrap=tk.WORD) #, width=80, height=20)
#         self.output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
#         self.detect_button = ttk.Button(self, text="Detect Details", width=14, command=self.detect_wde_deets)
#         self.detect_button.pack()
        
#         self.save_button = ttk.Button(self, text="Save", width=14, command=self.save_deets, state=tk.DISABLED)
#         self.save_button.pack()
        
#         self.clear_button = ttk.Button(self, text="Clear", width=14, command=self.clear_deets)
#         self.clear_button.pack()
        
#         self.map_button = ttk.Button(self, text="View Map", width=14, command=self.view_map, state=tk.DISABLED)
#         self.map_button.pack()
        
#         self.save_map_button = ttk.Button(self, text="Save Map", width=14, command=self.save_map, state=tk.DISABLED)
#         self.save_map_button.pack(pady=(0, 10))

#         self.desktop_info = None
    
#     def detect_wde_deets(self):
#         taskbar_info = get_taskbar_info()
#         monitors_info = get_monitors()
        
#         self.desktop_info = {
#             "taskbar": taskbar_info,
#             "monitors": [
#                 {
#                     "name": monitor.name,
#                     "width": monitor.width,
#                     "height": monitor.height,
#                     "x": monitor.x,
#                     "y": monitor.y
#                 }
#                 for monitor in monitors_info
#             ]
#         }
        
#         self.output_text.delete(1.0, tk.END)
#         self.output_text.insert(tk.END, json.dumps(self.desktop_info, indent=4))
        
#         self.save_button.config(state=tk.NORMAL)
#         self.map_button.config(state=tk.NORMAL)
    
#     def save_deets(self):
#         if not self.desktop_info:
#             messagebox.showwarning("No Data", "Please detect details first.")
#             return
        
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         default_filename = f"desktop_info_{timestamp}.json"
        
#         file_path = filedialog.asksaveasfilename(defaultextension=".json", initialfile=default_filename)
#         if file_path:
#             with open(file_path, 'w') as file:
#                 json.dump(self.desktop_info, file, indent=4)
#             messagebox.showinfo("Saved", f"Desktop info saved to {file_path}")
    
#     def clear_deets(self):
#         self.output_text.delete(1.0, tk.END)
#         self.desktop_info = None
#         self.save_button.config(state=tk.DISABLED)
#         self.map_button.config(state=tk.DISABLED)
    
#     def view_map(self):
#         if not self.desktop_info:
#             messagebox.showwarning("No Data", "Please detect details first.")
#             return

#         self.save_map_button.config(state=tk.NORMAL)

#         # Calculate the total width and height of the desktop environment
#         max_x = max(monitor["x"] + monitor["width"] for monitor in self.desktop_info["monitors"])
#         max_y = max(monitor["y"] + monitor["height"] for monitor in self.desktop_info["monitors"])
        
#         # Create a new image with the calculated dimensions
#         image = Image.new("RGB", (max_x, max_y), "white")
#         draw = ImageDraw.Draw(image)
        
#         # Draw monitors and legend labels
#         for monitor in self.desktop_info["monitors"]:
#             x, y = monitor["x"], monitor["y"]
#             width, height = monitor["width"], monitor["height"]
#             draw.rectangle((x, y, x + width, y + height), outline="blue", fill="lightblue")
            
#             # Create the legend label text
#             legend_text = f"Monitor: {monitor['name']}\nResolution: {width}x{height}\nPosition: ({x}, {y})"
            
#             # Draw the legend label using the default font
#             legend_x, legend_y = x + 10, y + 10
#             draw.text((legend_x, legend_y), legend_text, fill="black")
        
#         # Draw taskbar and legend label
#         taskbar_pos = self.desktop_info["taskbar"]["position"]
#         left, top, right, bottom = taskbar_pos
#         draw.rectangle(taskbar_pos, outline="red", fill="lightpink")
        
#         # Create the taskbar legend label text
#         taskbar_text = f"Taskbar\nPosition: ({left}, {top})\nSize: ({right-left}, {bottom-top})"
        
#         # Draw the taskbar legend label using the default font
#         taskbar_x, taskbar_y = left + 10, top + 10
#         draw.text((taskbar_x, taskbar_y), taskbar_text, fill="black")
        
#         # Display the image
#         image.show()

#     def save_map(self):
#         if not hasattr(self, 'map_image'):
#             messagebox.showwarning("No Map", "Please generate the map first.")
#             return
        
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         default_filename = f"desktop_map_{timestamp}.png"
        
#         file_path = filedialog.asksaveasfilename(defaultextension=".png", initialfile=default_filename)
#         if file_path:
#             self.map_image.save(file_path)
#             messagebox.showinfo("Saved", f"Desktop map saved to {file_path}")
    
        
# if __name__ == "__main__":
#     app = WDEDetectTool()
#     app.mainloop()