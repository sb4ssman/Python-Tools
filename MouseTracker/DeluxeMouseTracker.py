# -*- coding: utf-8 -*-
"""
Created on Wed Jul 16 16:53:43 2024

@author: Thomas
"""


# An unreasonably fancy mouse tracker


# Windows uses a virtual desktop that may not translate directly to the pixels of your montior(s) 
# They all line up 1:1, but a monitor's origin pixel is not necessarily Window's (0,0)


# desktop details should show taskbar presence and location 
    # want to draw a polygon showing the virtual space




import os
import re
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pyautogui
import threading
import time
import ctypes
from screeninfo import get_monitors
from datetime import datetime
from PIL import ImageGrab, ImageTk, Image, ImageDraw


# Import utilities from python_tools package
from utils.ToolTips import createToolTip, createNamedToolTip
from utils.TinyCheckbox import TinyCheckbox
from utils.FancyButtonTEST import FancyButton, LIGHT_COLORS, DARK_COLORS
from utils.OffsetCalibrator import calibrate_offset

# Get the directory of the app
app_directory = os.path.dirname(os.path.abspath(__file__))

# Change the current working directory to the script's directory
os.chdir(app_directory)

# Set settings path
settings_path = os.path.join(app_directory, "settings.json")



# Split self.geometry into coords and dimensions
def split_geometry(root):
    geometry = root.geometry()
    size, position = geometry.split('+', 1)
    width, height = map(int, size.split('x'))
    x, y = map(int, position.split('+'))
    return (x, y), (width, height)
# To use: coords, dimensions = split_geometry(self.root) 

# AppBarData structure
######################

class APPBARDATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("hWnd", ctypes.c_void_p),
        ("uCallbackMessage", ctypes.c_uint),
        ("uEdge", ctypes.c_uint),
        ("rc", ctypes.c_long * 4),
        ("lParam", ctypes.c_long),
    ]


# Settings
###################

class Settings:
    def __init__(self):
        self.settings_path = os.path.join(app_directory, "settings.json")
        self.default_settings = {
            "app_settings": {
            "win_offset_x": 0,
            "win_offset_y": 0,
            "always_advanced": False
        }}
        self.settings = self.load_settings()

    def load_settings(self):
        if os.path.exists(self.settings_path):
            with open(self.settings_path, 'r') as f:
                loaded_settings = json.load(f)
                # Ensure all default settings are present
                for key, value in self.default_settings.items():
                    if key not in loaded_settings:
                        loaded_settings[key] = value
                return loaded_settings
        return self.default_settings.copy()

    def save_settings(self):
        with open(self.settings_path, 'w') as f:
            json.dump(self.settings, f)

    def get(self, key):
        return self.settings.get(key, self.default_settings.get(key))

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()

# Global settings instance
settings = Settings()

# Update the global offset variables
WIN_OFFSET_X = settings.get("win_offset_x")
WIN_OFFSET_Y = settings.get("win_offset_y")

# The pre-app:
################
def check_settings_exist():
    print("Checking settings.json...")
    if not os.path.exists(settings_path):
        print("No settings found! Proceeding with warning and the simple tracker...")
        messagebox.showinfo("No Settings Found", "No settings file found.\nPlease calibrate the offset for accurate tracking.")

def start_appropriate_tracker(root):
    always_advanced = settings.get("always_advanced")
    print(f"Always Advanced setting: {always_advanced}")  # Debug print
    if always_advanced:
        print("Starting Advanced Mouse Tracker")
        return AdvancedMouseTracker(root)
    else:
        print("Starting Simple Mouse Tracker")
        return SimpleMouseTracker(root)




############################
#                          #
#   SIMPLE MOUSE TRACKER   #
#                          #
############################

class SimpleMouseTracker:
    def __init__(self, root, initial_x=None, initial_y=None):
        self.root = root
        self.root.title("MouseTracker")

        if initial_x is not None and initial_y is not None:
            self.root.geometry(f"165x185+{initial_x}+{initial_y}")
        else:
            self.root.geometry("165x185")
        
        self.root.minsize(160, 150)

        self.style = ttk.Style()
        self.style.theme_use("xpnative")

        self.theme_var = tk.StringVar(value="Clean")
        self.dark_mode_var = tk.BooleanVar(value=False)

        self.tracking_mouse = False
        self.mouse_position_after_id = None

        self.setup_gui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        global WIN_OFFSET_X, WIN_OFFSET_Y
        x_w, y_w = 0 - WIN_OFFSET_X, 0 - WIN_OFFSET_Y
        # print(f"Updated global offsets: WIN_OFFSET_X = {WIN_OFFSET_X}, WIN_OFFSET_Y = {WIN_OFFSET_Y}")
        self.mt_coordinates.config(text=f"Pixel:          (0, 0)\nWindows:  ({x_w}, {y_w})")
        
        print("Simple Mouse Tracker")

    def setup_gui(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(expand=False, padx=0, pady=0)
        # createToolTip(self.main_frame, "Grab anywhere on this tiny window to drag.")
        self.instructions = ttk.Label(self.main_frame, text="Grab anywhere to drag.", font=("", 8))
        self.instructions.pack(anchor="n", fill=tk.X, expand=False, padx=0, pady=0)

        self.simple_tracker_frame = ttk.Frame(self.main_frame)
        self.simple_tracker_frame.pack()

        self.simple_tracker_button = FancyButton(self.simple_tracker_frame, self.create_mouse_tracker_surface, self.theme_var, self.dark_mode_var, self.toggle_mouse_tracking)
        self.simple_tracker_button.outer_frame.pack()

        # Styling for small buttons:
        self.style = ttk.Style()
        self.style.theme_use("xpnative")
        self.style.configure('Link.TLabel', font=("", 8))
        self.style.map('Link.TLabel', foreground=[('hover', 'blue')])  # Change color to blue on hover

        # Frame to hold them
        self.little_frame = ttk.Frame(self.main_frame)
        self.little_frame.pack(fill=tk.X, padx=0, pady=0)
        self.little_frame.columnconfigure(0, weight=1)
        self.little_frame.columnconfigure(1, weight=1)

        self.calibrate_button = ttk.Button(self.little_frame, text="Calibrate", style="Link.TLabel", command=self.calibrate_offset)
        self.calibrate_button.grid(row=0, column=0, padx=0, pady=0, sticky="w")
        createToolTip(self.calibrate_button, "Calibrate the offset for accurate tracking.")

        self.advanced_button = ttk.Button(self.little_frame, text="Advanced", style="Link.TLabel", command=self.open_advanced_mode)
        self.advanced_button.grid(row=0, column=1, padx=0, pady=0, sticky="e")
        createToolTip(self.advanced_button, "More mouse tracking tools.")

        # Set ability to drag this tiny window around from anywhere
        self.root.bind('<Button-1>', self.start_move) # for dragging
        self.root.bind('<B1-Motion>', self.do_move)

        self.cancel_button = ttk.Button(self.main_frame, text="Cancel", width=8, command=self.on_closing)
        self.cancel_button.pack(padx=5, pady=5)

    # The fancy button
    def create_mouse_tracker_surface(self, surface):
        self.mt_title = ttk.Label(surface, text="Mouse Tracker", anchor="center", width=12, name="mt_title_font12")
        self.mt_title.pack(fill=tk.BOTH, padx=5, pady=5)
        ttk.Separator(surface, orient="horizontal").pack(fill=tk.X, padx=5, pady=0)
        self.mt_coordinates = ttk.Label(surface, text="Pixel:          (0, 0)\nWindows:  (0, 0)", anchor="w", name="mt_coordinates_font8")
        self.mt_coordinates.pack(fill=tk.X, padx=10, pady=2)
        self.mt_start = ttk.Label(surface, text="Start Tracking", anchor="center", name="mt_start_font10")
        self.mt_start.pack(fill=tk.BOTH, padx=5, pady=5, ipady=5)
        return surface.winfo_children()

    def settings_warn(self):
            if settings.is_first_run():
                messagebox.showinfo("Success", f"Batch path added to the list")
            self.calibrate_offset()
            settings.set_first_run_complete()



    # Do a calibrate
    def calibrate_offset(self):
        print("Calling OffsetCalibrator...")
        offsetX, offsetY = calibrate_offset()
        self.update_offset(offsetX, offsetY)

    def update_offset(self, offsetX, offsetY):
        global WIN_OFFSET_X, WIN_OFFSET_Y
        WIN_OFFSET_X = offsetX
        WIN_OFFSET_Y = offsetY
        settings.set("win_offset_x", offsetX)
        settings.set("win_offset_y", offsetY)
        x_w, y_w = 0 - WIN_OFFSET_X, 0 - WIN_OFFSET_Y
        print(f"Updated global offsets: X = {WIN_OFFSET_X}, Y = {WIN_OFFSET_Y}")
        self.mt_coordinates.config(text=f"Pixel:          (0, 0)\nWindows:  ({x_w}, {y_w})")
        
        self.update_notes_frame()
        
    def toggle_mouse_tracking(self):
        self.tracking_mouse = not self.tracking_mouse
        
        if self.tracking_mouse:
            print("Mouse Tracking: ACTIVE")
            self.mt_start.config(text="Stop Tracking")
            self.mouse_position()
        else:
            print("Mouse Tracking: DEACTIVATED")
            self.mt_start.config(text="Start Tracking")
            if self.mouse_position_after_id:
                self.root.after_cancel(self.mouse_position_after_id)
                self.mouse_position_after_id = None

    def mouse_position(self):
        global WIN_OFFSET_X, WIN_OFFSET_Y
        x_m, y_m = pyautogui.position()
        x_w, y_w = x_m - WIN_OFFSET_X, y_m - WIN_OFFSET_Y
        self.mt_coordinates.config(text=f"Pixel:          ({x_m},{y_m})\nWindows:  ({x_w},{y_w})")
        self.mouse_position_after_id = self.root.after(100, self.mouse_position)

    def open_advanced_mode(self):
        print("Enabling advanced mouse tracking interface...")
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        self.root.destroy()
        root = tk.Tk()
        AdvancedMouseTracker(root, initial_x=x, initial_y=y)
        root.mainloop()

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")
    
    def on_closing(self):
        if self.mouse_position_after_id:
            self.root.after_cancel(self.mouse_position_after_id)
        settings.save_settings()  # Save settings before closing
        self.root.destroy()





##############################
#                            #
#   ADVANCED MOUSE TRACKER   #
#                            #
##############################

class AdvancedMouseTracker:
    def __init__(self, root, initial_x=None, initial_y=None):
        self.root = root
        self.root.title("Advanced Mouse Tracker")
        
        if initial_x is not None and initial_y is not None:
            self.root.geometry(f"420x420+{initial_x}+{initial_y}")
        else:
            self.root.geometry("420x420")
        self.root.minsize(400, 221) # If you shrink the window to this minimum it lines up nicely

        self.style = ttk.Style()
        self.style.theme_use("xpnative")

        self.theme_var = tk.StringVar(value="Clean") 
        self.dark_mode_var = tk.BooleanVar(value=False)
        self.stay_on_top_var = tk.BooleanVar(value=False)
        self.arrow_keys_move_mouse = tk.BooleanVar(value=False)
        self.zoom_multiplier = tk.IntVar(value=16)
        self.always_advanced_var = tk.BooleanVar(value=settings.get("always_advanced")) # Default should be false

        self.tracker_active = False
        self.tracker_thread = False
        self.viewer_active = False  
        self.viewer_thread = None
        self.texture_image = None
        self.stop_thread = threading.Event()

        self.setup_gui()
        self.setup_texture()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        global WIN_OFFSET_X, WIN_OFFSET_Y
        x_w, y_w = 0 - WIN_OFFSET_X, 0 - WIN_OFFSET_Y
        # print(f"Updated global offsets: WIN_OFFSET_X = {WIN_OFFSET_X}, WIN_OFFSET_Y = {WIN_OFFSET_Y}")
        self.mt_coordinates.config(text=f"Pixel:          (0, 0)\nWindows:  ({x_w}, {y_w})")
        
        print("Advanced Mouse Tracker")

    def setup_gui(self):
        self.main_frame = ttk.Frame(self.root, padding=5)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)



        # Paned window
        self.paned_window = tk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL, sashwidth=5)
        self.paned_window.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Left frame (for coordinates list)
        self.left_frame = ttk.Frame(self.paned_window)
        self.left_frame.grid_columnconfigure(0, weight=1)
        self.left_frame.grid_rowconfigure(1, weight=1)

        # FancyButtons frame
        self.fancy_buttons_frame = ttk.Frame(self.left_frame)
        self.fancy_buttons_frame.grid(row=0, column=0, padx=(5, 0), pady=(5, 0), sticky="ew")
        self.fancy_buttons_frame.grid_columnconfigure(0, weight=1)

        self.tracker_button = FancyButton(self.fancy_buttons_frame, self.create_mouse_tracker_surface, self.theme_var, self.dark_mode_var, self.toggle_tracking)
        self.tracker_button.outer_frame.grid(row=0, column=0, padx=0, pady=0, sticky="ew")

        # mini frame for mini buttons
        self.mini_frame = ttk.Frame(self.fancy_buttons_frame)
        self.mini_frame.grid(row=1, column=0, padx=0, pady=0, sticky="ew")
        self.mini_frame.grid_columnconfigure(0, weight=1)  # Left column expands
        self.mini_frame.grid_columnconfigure(1, weight=1)  # Right column expands

        # Create the tiny checkbox
        self.always_advanced_cb = TinyCheckbox(
            self.mini_frame, 
            text="Always Advanced", 
            variable=self.always_advanced_var,
            command=self.toggle_always_advanced
        )
        self.always_advanced_cb.grid(row=0, column=0, padx=0, pady=0, sticky="w")

        # Make simple button look like a link
        self.style = ttk.Style()
        self.style.configure('Link.TLabel', background="#f0f0f0", font=("", 8))
        self.style.map('Link.TLabel', foreground=[('hover', 'blue')])  # Change color to blue on hover
        
        # Simple button
        self.simple_button = ttk.Button(self.mini_frame, text="Simple", style="Link.TLabel", command=self.open_simple_mode)
        self.simple_button.grid(row=0, column=1, padx=0, pady=0, sticky="e")
        createToolTip(self.simple_button, "Keep it simple.")

        # Create a frame to hold the listbox, scrollbar, and controls
        self.listbox_container = ttk.Frame(self.left_frame)
        self.listbox_container.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        self.listbox_container.grid_columnconfigure(0, weight=1)
        self.listbox_container.grid_rowconfigure(1, weight=1)

        self.coordinates_label = ttk.Label(self.listbox_container, text="Caught Coordinates: (0)")
        self.coordinates_label.grid(row=0, column=0, padx=0, pady=0, sticky="ew")

        self.listbox_frame = ttk.Frame(self.listbox_container)
        self.listbox_frame.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")
        self.listbox_frame.grid_columnconfigure(0, weight=1)
        self.listbox_frame.grid_rowconfigure(0, weight=1)

        self.coordinates_listbox = tk.Listbox(self.listbox_frame)
        self.coordinates_listbox.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        self.coordinates_listbox.bind('<<ListboxSelect>>', self.on_coordinate_select)

        scrollbar = ttk.Scrollbar(self.listbox_frame, orient="vertical", command=self.coordinates_listbox.yview)
        scrollbar.grid(row=0, column=1, padx=0, pady=0, sticky="ns")
        self.coordinates_listbox.configure(yscrollcommand=scrollbar.set)

        self.list_controls_frame = ttk.Frame(self.left_frame)
        self.list_controls_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        self.list_controls_frame.grid_columnconfigure(0, weight=1)
        self.list_controls_frame.grid_columnconfigure(1, weight=1)

        self.save_button = ttk.Button(self.list_controls_frame, text="Save", command=self.save_coordinates, width=7)
        self.save_button.grid(row=0, column=0, padx=5, pady=(0, 5), sticky="e")

        self.clear_button = ttk.Button(self.list_controls_frame, text="Clear", command=self.clear_coords, width=7)
        self.clear_button.grid(row=0, column=1, padx=5, pady=(0, 5), sticky="w")


        # Right frame
        self.right_frame = ttk.Frame(self.paned_window)
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(1, weight=1)

        # home frame
        self.home_frame = ttk.Frame(self.right_frame)
        self.home_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 5))
        self.home_frame.columnconfigure([0, 1, 2, 3, 4], weight=1)

        # Instructions label
        self.instructions_hover = ttk.Label(self.home_frame, text="[Hover for info]")
        self.instructions_hover.grid(row=0, column=0, columnspan=2, sticky="w", padx=0, pady=0)
        createToolTip(self.instructions_hover, "Instructions: Activate the tracker and/or viewer.\n"
                                                "Press C to catch coordinates while tracking.\n"
                                                "Calibrate offset or view environment details.\n"
                                                "Locate a coordinate. Click captured coords\n"
                                                "to see them located again.")

        # Stay on top
        self.stay_on_top_checkbox = ttk.Checkbutton(self.home_frame, text="Stay on Top", variable=self.stay_on_top_var, command=self.toggle_stay_on_top)
        self.stay_on_top_checkbox.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=(5, 0), pady=0)
        createToolTip(self.stay_on_top_checkbox, text="Set this to keep the window on top.")

        # Arrows move mouse
        self.arrow_keys_checkbox = ttk.Checkbutton(self.home_frame, text="Arrow keys move mouse", variable=self.arrow_keys_move_mouse, command=self.toggle_arrow_keys)
        self.arrow_keys_checkbox.grid(row=2, column=0, columnspan=5, sticky=tk.W, padx=(5, 0), pady=0)
        createToolTip(self.arrow_keys_checkbox, text="Use arrow keys or WASD to nudge the mouse.")

        # Zoom dropdown
        zoom_label = ttk.Label(self.home_frame, text="1px =")
        zoom_label.grid(row=0, column=3, padx=(6,0), pady=5, sticky="e") # Extra pixel for alignment
        createToolTip(zoom_label, "Select pixel multiplier.\n" \
                                    "You can input integer values, and\n" \
                                    "you can resize the window to view\n" \
                                    "more of the area around your mouse." \
                                    )

        zoom_dropdown = ttk.Combobox(self.home_frame, textvariable=self.zoom_multiplier, values=[1, 2, 3, 4, 8, 16, 32, 64, 128], width=3)
        zoom_dropdown.grid(row=0, column=4, padx=(5, 0), pady=0, sticky="w")
        zoom_dropdown.current(5)  # default value = 16

        # Toggle viewer button
        self.viewer_toggle_button = ttk.Button(self.home_frame, text="Viewer [Off]", width=13, command=self.toggle_viewer)
        self.viewer_toggle_button.grid(row=1, column=3, columnspan=2, padx=0, pady=0)


        # Zoomed view
        self.zoomed_frame = ttk.Frame(self.right_frame, borderwidth=1)
        self.zoomed_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5), pady=0)
        self.zoomed_frame.grid_columnconfigure(0, weight=1)
        self.zoomed_frame.grid_rowconfigure(0, weight=1)

        self.zoomed_canvas = tk.Canvas(self.zoomed_frame, bg='grey', highlightthickness=0)
        self.zoomed_canvas.grid(row=0, column=0, sticky="nsew")

        self.setup_texture()

        # Notes
        self.notes_frame = ttk.LabelFrame(self.right_frame, text="Notes:")
        self.notes_frame.grid(row=2, column=0, sticky="nw", padx=5, pady=5)

        # win_offset_x, win_offset_y = self.settings["app_settings"]["win_offset_x"], 0 - self.settings["app_settings"]["win_offset_y"] # Get from settings
        win_x, win_y = 0 - WIN_OFFSET_X, 0 - WIN_OFFSET_Y # calc win coords

        notes_text = f"Windows Offset: {WIN_OFFSET_X}, {WIN_OFFSET_Y}\n" \
                        "Primary monitor origin: (0, 0)\n" \
                        f"@ windows coord: ({win_x}, {win_y})"

        self.notes_label = ttk.Label(self.notes_frame, text=notes_text)
        self.notes_label.pack(anchor="nw", padx=0, pady=0)



        # Add frames to paned window
        self.paned_window.add(self.left_frame, width=200, padx=0, pady=0)
        self.paned_window.add(self.right_frame, padx=0, pady=0)



        # Auxiliary frame
        self.aux_frame = ttk.Frame(self.main_frame)
        self.aux_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        self.aux_frame.grid_columnconfigure(2, weight=1)

        # Additional buttons
        self.calibrate_button = ttk.Button(self.aux_frame, text="Calibrate\nOffset", command=self.calibrate_offset)
        self.calibrate_button.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.monitor_info_button = ttk.Button(self.aux_frame, text="Get Virtual\nDesktop Details...", command=self.get_monitor_info)
        self.monitor_info_button.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Locate coordinate FancyButton - NOT FANCY right now
        self.locate_frame = ttk.Frame(self.aux_frame)
        self.locate_frame.grid(row=0, column=2, sticky="w", padx=(10, 5), pady=0)

        self.locate_label = ttk.Label(self.locate_frame, text="Locate Coordinate", anchor="center")
        self.locate_label.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0,0))
        
        self.locate_label_entry_frame = ttk.Frame(self.locate_frame)
        self.locate_label_entry_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=0)
        
        self.locate_x_entry = ttk.Entry(self.locate_label_entry_frame, width=10)
        self.locate_x_entry.pack(side=tk.LEFT, expand=True)
        ttk.Label(self.locate_label_entry_frame, text=",").pack(side=tk.LEFT, padx=0)
        self.locate_y_entry = ttk.Entry(self.locate_label_entry_frame, width=10)
        self.locate_y_entry.pack(side=tk.LEFT, expand=True)
        
        self.locate_button = ttk.Button(self.locate_label_entry_frame, text="Find", width=6, command=self.locate_coordinate)
        self.locate_button.pack(side=tk.RIGHT, expand=False, padx=(5, 0), pady=0)


# Commented off while FancyButton leaks
        # self.locate_coord_button = FancyButton(self.locate_frame, self.create_locate_coord_surface, self.theme_var, self.dark_mode_var, self.locate_coordinate)
        # self.locate_coord_button.outer_frame.pack(expand=False)


        # # Set minimum sizes for critical widgets
        # self.root.update_idletasks()
        # self.list_controls_frame.update_idletasks()
        # self.notes_frame.update_idletasks()
        # self.aux_frame.update_idletasks()

        # min_height = self.list_controls_frame.winfo_reqheight() + self.notes_frame.winfo_reqheight() + self.aux_frame.winfo_reqheight() + 100  # Extra space for padding
        # self.root.minsize(300, min_height)

        # Bind C to catch
        self.root.bind("<c>", lambda event: self.catch_coordinate())



# Advanced definitions and methods
###################################

    def toggle_always_advanced(self):
        settings.set("always_advanced", self.always_advanced_var.get())

    # Do a calibrate
    def calibrate_offset(self):
        print("Calling OffsetCalibrator...")
        offsetX, offsetY = calibrate_offset()
        self.update_offset(offsetX, offsetY)

    def update_offset(self, offsetX, offsetY):
        global WIN_OFFSET_X, WIN_OFFSET_Y
        WIN_OFFSET_X = offsetX
        WIN_OFFSET_Y = offsetY
        settings.set("win_offset_x", offsetX)
        settings.set("win_offset_y", offsetY)
        x_w, y_w = 0 - WIN_OFFSET_X, 0 - WIN_OFFSET_Y
        print(f"Updated global offsets: X = {WIN_OFFSET_X}, Y = {WIN_OFFSET_Y}")
        self.mt_coordinates.config(text=f"Pixel:          (0, 0)\nWindows:  ({x_w}, {y_w})")
        
        self.update_notes_frame()

    def update_notes_frame(self):
        global WIN_OFFSET_X, WIN_OFFSET_Y
        win_x, win_y = 0 - WIN_OFFSET_X, 0 - WIN_OFFSET_Y
        notes_text = f"Windows Offset: {WIN_OFFSET_X}, {WIN_OFFSET_Y}\n" \
                     "Primary monitor origin: (0, 0)\n" \
                     f"@ windows coord: ({win_x}, {win_y})"
        self.notes_label.config(text=notes_text)
        print("Updated notes frame with new offset information")

    def toggle_stay_on_top(self):
        print(f"Stay on top: {self.stay_on_top_var.get()}")
        self.root.attributes('-topmost', self.stay_on_top_var.get())

    def center_panes(self):
        self.root.update_idletasks()
        self.paned_window.sashpos(0, self.root.winfo_width() // 2)
        self.right_paned_window.sashpos(0, self.right_frame.winfo_height() // 2)

    def on_closing(self):
        self.stop_viewer_update()
        if self.mouse_position_after_id:
            self.root.after_cancel(self.mouse_position_after_id)
        self.root.destroy()

    def create_mouse_tracker_surface(self, surface):
        self.mt_title = ttk.Label(surface, text="Mouse Tracker", anchor="center", width=12, name="mt_title_font12")
        self.mt_title.pack(fill=tk.BOTH, padx=5, pady=5)
        ttk.Separator(surface, orient="horizontal").pack(fill=tk.X, padx=5, pady=0)
        self.mt_coordinates = ttk.Label(surface, text="Pixel:          (0, 0)\nWindows:  (0, 0)", anchor="w", name="mt_coordinates_font8")
        self.mt_coordinates.pack(fill=tk.X, padx=10, pady=2)
        self.mt_start = ttk.Label(surface, text="Start Tracking", anchor="center", name="mt_start_font10")
        self.mt_start.pack(fill=tk.BOTH, padx=5, pady=5, ipady=5)
        return surface.winfo_children()

# Commented off while FancyButton leaks
    # def create_locate_coord_surface(self, surface):
    #     self.locate_label = ttk.Label(surface, text="Locate Coordinate", anchor="center")
    #     self.locate_label.pack(fill=tk.X, padx=5, pady=(5,0))
        
    #     self.locate_label_entry_frame = ttk.Frame(surface)
    #     self.locate_label_entry_frame.pack(fill=tk.X, padx=5, pady=(2,5))
        
    #     self.locate_x_entry = ttk.Entry(self.locate_label_entry_frame, width=10)
    #     self.locate_x_entry.pack(side=tk.LEFT, expand=True)
    #     ttk.Label(self.locate_label_entry_frame, text=",").pack(side=tk.LEFT, padx=0)
    #     self.locate_y_entry = ttk.Entry(self.locate_label_entry_frame, width=10)
    #     self.locate_y_entry.pack(side=tk.LEFT, expand=True)
        
    #     return surface.winfo_children()


    def toggle_arrow_keys(self):
        if self.arrow_keys_move_mouse.get():
            self.root.focus_set()  # Set focus to the main window to capture key events
            self.bind_arrow_keys()
        else:
            self.unbind_arrow_keys()

    def bind_arrow_keys(self):
        self.root.bind('<Left>', self.move_mouse)
        self.root.bind('<Right>', self.move_mouse)
        self.root.bind('<Up>', self.move_mouse)
        self.root.bind('<Down>', self.move_mouse)
        self.root.bind('<a>', self.move_mouse)
        self.root.bind('<d>', self.move_mouse)
        self.root.bind('<w>', self.move_mouse)
        self.root.bind('<s>', self.move_mouse)

    def unbind_arrow_keys(self):
        self.root.unbind('<Left>')
        self.root.unbind('<Right>')
        self.root.unbind('<Up>')
        self.root.unbind('<Down>')
        self.root.unbind('<a>')
        self.root.unbind('<d>')
        self.root.unbind('<w>')
        self.root.unbind('<s>')

    def move_mouse(self, event):
        if self.arrow_keys_move_mouse.get():
            x, y = pyautogui.position()
            move_distance = 1

            if event.keysym in ['Left', 'a']:
                x -= move_distance
            elif event.keysym in ['Right', 'd']:
                x += move_distance
            elif event.keysym in ['Up', 'w']:
                y -= move_distance
            elif event.keysym in ['Down', 's']:
                y += move_distance

            pyautogui.moveTo(x, y)
            self.update_mouse_position()


    def setup_texture(self):
        self.zoomed_canvas.bind("<Configure>", self.on_zoomed_canvas_resize)
        # Initial creation of the texture
        self.on_zoomed_canvas_resize(None)

    def on_zoomed_canvas_resize(self, event):
        if event:
            width, height = event.width, event.height
        else:
            width, height = self.zoomed_canvas.winfo_width(), self.zoomed_canvas.winfo_height()

        block_size = 20
        checkerboard = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(checkerboard)
        for y in range(0, height, block_size):
            for x in range(0, width, block_size):
                color = (69, 69, 69) if (x // block_size + y // block_size) % 2 == 0 else (255, 255, 255)
                draw.rectangle([x, y, x + block_size, y + block_size], fill=color)

        self.texture_tk = ImageTk.PhotoImage(checkerboard)
        if self.texture_image:
            self.zoomed_canvas.delete(self.texture_image)
        self.texture_image = self.zoomed_canvas.create_image(0, 0, anchor=tk.NW, image=self.texture_tk, tags="texture")


    def update_viewer_thread(self):
        while not self.stop_thread.is_set():
            if self.viewer_active:
                x, y = pyautogui.position()
                self.root.after(0, lambda: self.update_zoomed_view(None, x, y))
            time.sleep(0.1)

    def toggle_viewer(self):
        self.viewer_active = not self.viewer_active
        if self.viewer_active:
            self.viewer_toggle_button.config(text="Viewer [WAIT]")
            self.zoomed_canvas.itemconfigure(self.texture_image, state='hidden')
            self.start_viewer_update()
        else:
            self.viewer_toggle_button.config(text="Viewer [WAIT]")
            self.stop_viewer_update()
            self.zoomed_canvas.itemconfigure(self.texture_image, state='normal')

    def start_viewer_update(self):
        if not self.viewer_thread:
            self.stop_thread.clear()
            self.viewer_thread = threading.Thread(target=self.update_viewer_thread)
            self.viewer_thread.daemon = True
            self.viewer_thread.start()
            self.root.after(100, self.check_viewer_thread_started)

    def stop_viewer_update(self):
        if self.viewer_thread:
            self.stop_thread.set()
            self.root.after(100, self.check_viewer_thread_stopped)

    def update_viewer_thread(self):
        while not self.stop_thread.is_set():
            if self.viewer_active:
                x, y = pyautogui.position()
                self.root.after(0, lambda: self.update_zoomed_view(x, y))
            time.sleep(0.1)

    def check_viewer_thread_started(self):
        if self.viewer_thread.is_alive():
            self.viewer_active = True
            self.viewer_toggle_button.config(text="Viewer [On]")
        else:
            self.root.after(100, self.check_viewer_thread_started)

    def check_viewer_thread_stopped(self):
        if not self.viewer_thread.is_alive():
            self.viewer_thread = None
            self.viewer_active = False
            self.viewer_toggle_button.config(text="Viewer [Off]")
            self.zoomed_canvas.itemconfigure(self.texture_image, state='normal')
        else:
            self.root.after(100, self.check_viewer_thread_stopped)

    def update_zoomed_view(self, event=None, x=None, y=None):
        if not self.viewer_active:
            return

        try:
            if x is None or y is None:
                x, y = pyautogui.position()
            
            zoom = max(1, int(self.zoom_multiplier.get()))
            canvas_width = self.zoomed_canvas.winfo_width()
            canvas_height = self.zoomed_canvas.winfo_height()

            region_width = (canvas_width // zoom) | 1
            region_height = (canvas_height // zoom) | 1

            region_x = x - region_width // 2
            region_y = y - region_height // 2

            im = pyautogui.screenshot(region=(region_x, region_y, region_width, region_height))
            
            zoomed_width = region_width * zoom
            zoomed_height = region_height * zoom
            zoomed_im = im.resize((zoomed_width, zoomed_height), Image.NEAREST)
            self.zoomed_im_tk = ImageTk.PhotoImage(zoomed_im)

            self.zoomed_canvas.delete("zoomed_image")
            self.zoomed_canvas.delete("crosshair")

            offset_x = (canvas_width - zoomed_width) // 2
            offset_y = (canvas_height - zoomed_height) // 2

            self.zoomed_canvas.create_image(offset_x, offset_y, anchor=tk.NW, image=self.zoomed_im_tk, tags="zoomed_image")

            center_x = offset_x + zoomed_width // 2
            center_y = offset_y + zoomed_height // 2

            left = center_x - zoom // 2 - 1
            right = center_x + (zoom + 1) // 2
            top = center_y - zoom // 2 - 1
            bottom = center_y + (zoom + 1) // 2

            self.zoomed_canvas.create_line(left, offset_y, left, offset_y + zoomed_height, fill="red", tags="crosshair")
            self.zoomed_canvas.create_line(right, offset_y, right, offset_y + zoomed_height, fill="red", tags="crosshair")
            self.zoomed_canvas.create_line(offset_x, top, offset_x + zoomed_width, top, fill="red", tags="crosshair")
            self.zoomed_canvas.create_line(offset_x, bottom, offset_x + zoomed_width, bottom, fill="red", tags="crosshair")

        except Exception as e:
            print(f"Error in update_zoomed_view: {e}")



    def toggle_tracking(self):
        self.tracking_mouse = not self.tracking_mouse
        if self.tracking_mouse:
            self.mt_start.config(text="Stop Tracking")
            self.update_mouse_position()
        else:
            self.mt_start.config(text="Start Tracking")
            if self.mouse_position_after_id:
                self.root.after_cancel(self.mouse_position_after_id)
                self.mouse_position_after_id = None

    def update_mouse_position(self):
        x_m, y_m = pyautogui.position()
        x_w, y_w = x_m - WIN_OFFSET_X, y_m - WIN_OFFSET_Y
        self.mt_coordinates.config(text=f"Pixel:          ({x_m},{y_m})\nWindows:  ({x_w},{y_w})")
        self.mouse_position_after_id = self.root.after(100, self.update_mouse_position)

    def catch_coordinate(self):
        if self.tracking_mouse:
            x_m, y_m = pyautogui.position()
            x_w, y_w = x_m - WIN_OFFSET_X, y_m - WIN_OFFSET_Y
            coordinate = f"Pixel: ({x_m},{y_m}), Windows: ({x_w},{y_w})"
            self.caught_coordinates.append(coordinate)
            self.coordinates_listbox.insert(tk.END, coordinate)
            self.update_coordinates_label()

    def update_coordinates_label(self):
        count = len(self.caught_coordinates)
        self.coordinates_label.config(text=f"Caught Coordinates: ({count})")

    def save_coordinates(self):
        if not self.caught_coordinates:
            messagebox.showwarning("No Coordinates", "No coordinates to save.")
            return

        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"coordinates_{now}.txt"
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=filename, filetypes=[("Text files", "*.txt")])
        
        if file_path:
            with open(file_path, 'w') as f:
                for coord in self.caught_coordinates:
                    f.write(f"{coord}\n")
            messagebox.showinfo("Save Successful", f"Coordinates saved to {file_path}")

    def clear_coords(self):
        self.caught_coordinates.clear()
        self.coordinates_listbox.delete(0, tk.END)
        self.update_coordinates_label()

    def on_coordinate_select(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            coordinate = event.widget.get(index)
            parts = coordinate.split(", ")
            pixel_part = parts[0].split(": ")[1].strip("()")
            x, y = map(int, pixel_part.split(","))
            self.update_zoomed_view(x, y)
            self.draw_crosshair(x, y)

    def locate_coordinate(self):
        try:
            x = int(self.locate_x_entry.get())
            y = int(self.locate_y_entry.get())
            self.draw_overlay_crosshair(x, y)
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid integer coordinates.")

    def draw_overlay_crosshair(self, x, y):
        screen_width, screen_height = pyautogui.size()
        overlay = tk.Toplevel(self.root)
        overlay.overrideredirect(True)
        overlay.geometry(f"{screen_width}x{screen_height}+0+0")
        overlay.attributes('-topmost', True)
        overlay.attributes('-alpha', 0.3)

        canvas = tk.Canvas(overlay, width=screen_width, height=screen_height, highlightthickness=0)
        canvas.pack()

        # Draw semi-transparent overlay
        canvas.create_rectangle(0, 0, screen_width, screen_height, fill='gray', stipple='gray50')
        self.draw_crosshair(x, y)  # Draw the small crosshair sprite
        self.root.after(2000, overlay.destroy)


    def draw_crosshair(self, x, y):
        print(f"Plotting crosshair @ ({x}, {y})")
        size = 70  # Size of the crosshair window
        crosshair = tk.Toplevel(self.root)
        crosshair.overrideredirect(True)
        crosshair.geometry(f"{size}x{size}+{x-size//2}+{y-size//2}")
        crosshair.attributes('-topmost', True)
        crosshair.attributes('-transparentcolor', 'white')
        
        canvas = tk.Canvas(crosshair, width=size, height=size, highlightthickness=0, bg='white')
        canvas.pack()

        center = size // 2

        # Draw exact 3x3 square outline surrounding the critical pixel
        canvas.create_rectangle(center-1, center-1, center+1, center+1, outline="red", width=1)

        # Draw isosceles triangles
        triangle_base = 13
        triangle_height = 20
        gap = 5  # 5-pixel gap from the edge of the 3x3 square

        # Top triangle
        canvas.create_polygon(
            center, center - gap - 1,
            center - triangle_base//2, center - gap - triangle_height - 1,
            center + triangle_base//2, center - gap - triangle_height - 1,
            fill="red", outline="red"
        )

        # Bottom triangle
        canvas.create_polygon(
            center, center + gap + 1,
            center - triangle_base//2, center + gap + triangle_height + 1,
            center + triangle_base//2, center + gap + triangle_height + 1,
            fill="red", outline="red"
        )

        # Left triangle
        canvas.create_polygon(
            center - gap - 1, center,
            center - gap - triangle_height - 1, center - triangle_base//2,
            center - gap - triangle_height - 1, center + triangle_base//2,
            fill="red", outline="red"
        )

        # Right triangle
        canvas.create_polygon(
            center + gap + 1, center,
            center + gap + triangle_height + 1, center - triangle_base//2,
            center + gap + triangle_height + 1, center + triangle_base//2,
            fill="red", outline="red"
        )
        
        self.root.after(2000, crosshair.destroy)








    # Desktop environment details
    def get_monitor_info(self):
        x_w, y_w = 0 - WIN_OFFSET_X, 0 - WIN_OFFSET_Y
        monitors = get_monitors()
        info = "Monitor Information:\n\n"
        for i, monitor in enumerate(monitors):
            info += f"Monitor {i+1}:\n"
            info += f"  Name: {monitor.name}\n"
            info += f"  Resolution: {monitor.width}x{monitor.height}\n"
            info += f"  Position: ({monitor.x}, {monitor.y})\n\n"
            info += f"Windows offset: {WIN_OFFSET_X}, {WIN_OFFSET_Y}\n\n"
            info += f"Primary monitor origin\ncoordinate in Windows\nvirtual desktop: ({x_w}, {y_w})"
        messagebox.showinfo("Monitor Info", info)

    def get_taskbar_info(self):
        taskbar_edge = self.get_taskbar_edge()
        taskbar_rect = self.get_taskbar_rect()
        info = f"Taskbar Edge: {taskbar_edge}\n"
        info += f"Taskbar Rectangle: {taskbar_rect}"
        messagebox.showinfo("Taskbar Info", info)

    def get_taskbar_edge(self):
        appbardata = APPBARDATA()
        appbardata.cbSize = ctypes.sizeof(appbardata)
        ctypes.windll.shell32.SHAppBarMessage(4, ctypes.byref(appbardata))
        edges = {0: "Left", 1: "Top", 2: "Right", 3: "Bottom"}
        return edges.get(appbardata.uEdge, "Unknown")

    def get_taskbar_rect(self):
        appbardata = APPBARDATA()
        appbardata.cbSize = ctypes.sizeof(appbardata)
        ctypes.windll.shell32.SHAppBarMessage(4, ctypes.byref(appbardata))
        return tuple(appbardata.rc)

    # Return to simplicity
    def open_simple_mode(self):
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        self.root.destroy()
        root = tk.Tk()
        SimpleMouseTracker(root, initial_x=x, initial_y=y)
        root.mainloop()

    def on_closing(self):
        self.stop_viewer_update()
        if self.mouse_position_after_id:
            self.root.after_cancel(self.mouse_position_after_id)
        settings.save_settings()  # Save settings before closing
        self.root.destroy()


# In your main script:
if __name__ == "__main__":
    root = tk.Tk()
    check_settings_exist()
    app = start_appropriate_tracker(root)
    root.mainloop()