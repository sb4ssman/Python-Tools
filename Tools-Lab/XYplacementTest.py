# -*- coding: utf-8 -*-
"""
Created on Tue Jul 09 19:24:28 2024

@author: Thomas
"""




import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import time
import pyautogui
import pygetwindow as gw
import json
from datetime import datetime
from monitorinfoexhelper import get_monitors_info
from wde_map_generator import generate_map, show_mouse_position
from PIL import ImageTk, Image
import tempfile

class AdvancedPlacementTool(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Advanced Windows Placement Test Tool")
        self.geometry("1000x700")
        
        self.desktop_info = None
        self.offset_x, self.offset_y = 0, 0
        self.zoom_level = 1.0
        self.base_map = None
        self.create_gui()

    def create_gui(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Test tab
        self.test_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.test_frame, text="Placement Test")
        self.create_test_tab()

        # Monitor Info tab
        self.monitor_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.monitor_frame, text="Monitor Info")
        self.create_monitor_tab()

        # Map tab
        self.map_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.map_frame, text="Desktop Map")
        self.create_map_tab()

        # Calibration tab
        self.calibration_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.calibration_frame, text="Offset Calibration")
        self.create_calibration_tab()

    def create_test_tab(self):
        # Test points
        self.test_points_frame = ttk.LabelFrame(self.test_frame, text="Test Points")
        self.test_points_frame.pack(fill=tk.X, padx=10, pady=5)

        self.test_points = []
        for i in range(4):
            point_frame = ttk.Frame(self.test_points_frame)
            point_frame.pack(fill=tk.X, padx=5, pady=2)

            ttk.Label(point_frame, text=f"Point {i+1} X:").pack(side=tk.LEFT)
            x_entry = ttk.Entry(point_frame, width=10)
            x_entry.pack(side=tk.LEFT, padx=(0, 5))

            ttk.Label(point_frame, text="Y:").pack(side=tk.LEFT)
            y_entry = ttk.Entry(point_frame, width=10)
            y_entry.pack(side=tk.LEFT)

            self.test_points.append((x_entry, y_entry))

        # Test button
        self.test_button = ttk.Button(self.test_frame, text="Run Placement Tests", command=self.run_placement_tests)
        self.test_button.pack(pady=10)

        # Results
        self.results_text = tk.Text(self.test_frame, wrap=tk.WORD, height=20)
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def create_monitor_tab(self):
        self.monitor_text = tk.Text(self.monitor_frame, wrap=tk.WORD)
        self.monitor_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.refresh_button = ttk.Button(self.monitor_frame, text="Refresh Monitor Info", command=self.refresh_monitor_info)
        self.refresh_button.pack(pady=5)

    def create_map_tab(self):
        self.map_canvas = tk.Canvas(self.map_frame)
        self.map_canvas.pack(fill=tk.BOTH, expand=True)

        self.update_map_button = ttk.Button(self.map_frame, text="Update Map", command=self.update_map)
        self.update_map_button.pack(pady=5)

        # Bind mouse wheel event to zoom function
        self.map_canvas.bind("<MouseWheel>", self.zoom_map)


    def create_calibration_tab(self):
        ttk.Label(self.calibration_frame, text="Offset Calibration", font=("", 16)).pack(pady=10)
        ttk.Label(self.calibration_frame, text="Click 'Calibrate' to detect the offset between\nWindows virtual desktop origin and primary monitor origin.").pack()
        
        self.calibrate_button = ttk.Button(self.calibration_frame, text="Calibrate", command=self.calibrate_offset)
        self.calibrate_button.pack(pady=20)

        self.offset_label = ttk.Label(self.calibration_frame, text="Current Offset: Not Calibrated")
        self.offset_label.pack()

    def run_placement_tests(self):
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Running placement tests...\n\n")

        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as temp_file:
            temp_file.write("This is a temporary file for window placement testing.")
            temp_file_path = temp_file.name

        try:
            for i, (x_entry, y_entry) in enumerate(self.test_points):
                try:
                    x = int(x_entry.get())
                    y = int(y_entry.get())
                except ValueError:
                    self.results_text.insert(tk.END, f"Invalid coordinates for Point {i+1}. Skipping.\n")
                    continue

                self.results_text.insert(tk.END, f"Testing Point {i+1}: ({x}, {y})\n")
                self.test_window_placement(temp_file_path, x, y)
                self.results_text.insert(tk.END, "\n")

        finally:
            # Close and remove the temporary file
            os.unlink(temp_file_path)

        self.results_text.insert(tk.END, "All tests completed.")

    def test_window_placement(self, file_path, x, y):
        # Open the file
        os.startfile(file_path)
        time.sleep(1)  # Wait for the application to open

        # Get the window
        windows = gw.getWindowsWithTitle(os.path.basename(file_path))
        if not windows:
            self.results_text.insert(tk.END, "Error: Window not found.\n")
            return

        window = windows[0]

        # Record initial position
        initial_pos = window.left, window.top
        self.results_text.insert(tk.END, f"Initial window position: {initial_pos}\n")

        # Move the window
        window.moveTo(x, y)
        time.sleep(0.5)  # Wait for the move to complete

        # Record new position
        new_pos = window.left, window.top
        self.results_text.insert(tk.END, f"New window position: {new_pos}\n")

        # Calculate and display offset
        offset_x = new_pos[0] - x
        offset_y = new_pos[1] - y
        self.results_text.insert(tk.END, f"Offset from requested position: ({offset_x}, {offset_y})\n")

        # Calculate position relative to calibrated offset
        relative_x = new_pos[0] - self.offset_x
        relative_y = new_pos[1] - self.offset_y
        self.results_text.insert(tk.END, f"Position relative to calibrated offset: ({relative_x}, {relative_y})\n")

        # Get monitor information
        monitor_info = self.get_monitor_info_for_position(new_pos[0], new_pos[1])
        if monitor_info:
            self.results_text.insert(tk.END, f"Monitor: {monitor_info['device_name']}\n")
            self.results_text.insert(tk.END, f"Monitor bounds: {monitor_info['screen_coords']}\n")
        else:
            self.results_text.insert(tk.END, "Error: Could not determine monitor information for the given position.\n")

        # Close the window
        window.close()

    def get_monitor_info_for_position(self, x, y):
        if not self.desktop_info:
            self.refresh_monitor_info()
        
        for monitor in self.desktop_info["monitors"]:
            left, top, right, bottom = monitor["screen_coords"]
            if left <= x < right and top <= y < bottom:
                return monitor
        return None

    def refresh_monitor_info(self):
        self.desktop_info = {"monitors": get_monitors_info()}
        self.monitor_text.delete(1.0, tk.END)
        self.monitor_text.insert(tk.END, json.dumps(self.desktop_info, indent=4))
        self.update_map()

    def update_map(self):
        if not self.desktop_info:
            self.refresh_monitor_info()

        self.base_map = generate_map(self.desktop_info, show_grid=True, show_numbers=True, show_legend=True, mark_origin=True)
        self.display_map()

    def display_map(self):
        if self.base_map:
            # Apply zoom
            zoomed_size = (int(self.base_map.width * self.zoom_level), int(self.base_map.height * self.zoom_level))
            zoomed_map = self.base_map.copy()
            zoomed_map = zoomed_map.resize(zoomed_size, Image.LANCZOS)

            # Fit to canvas
            canvas_width = self.map_canvas.winfo_width()
            canvas_height = self.map_canvas.winfo_height()
            zoomed_map.thumbnail((canvas_width, canvas_height), Image.LANCZOS)

            self.map_photo = ImageTk.PhotoImage(zoomed_map)
            self.map_canvas.delete("all")
            self.map_canvas.create_image(0, 0, anchor=tk.NW, image=self.map_photo)

            # Start updating mouse position
            self.update_mouse_position()

    def update_mouse_position(self):
        if self.desktop_info and self.base_map:
            mouse_x, mouse_y = pyautogui.position()
            map_with_mouse = show_mouse_position(self.base_map.copy(), mouse_x, mouse_y)
            
            # Apply zoom
            zoomed_size = (int(map_with_mouse.width * self.zoom_level), int(map_with_mouse.height * self.zoom_level))
            map_with_mouse = map_with_mouse.resize(zoomed_size, Image.LANCZOS)

            # Fit to canvas
            canvas_width = self.map_canvas.winfo_width()
            canvas_height = self.map_canvas.winfo_height()
            map_with_mouse.thumbnail((canvas_width, canvas_height), Image.LANCZOS)

            self.map_photo = ImageTk.PhotoImage(map_with_mouse)
            self.map_canvas.delete("all")
            self.map_canvas.create_image(0, 0, anchor=tk.NW, image=self.map_photo)
            
            # Update mouse position text
            self.map_canvas.create_text(10, 10, anchor=tk.NW, text=f"Mouse: ({mouse_x}, {mouse_y})", tags="mouse_pos_text")
            
        self.after(100, self.update_mouse_position)

    def zoom_map(self, event):
        if event.delta > 0:
            self.zoom_level *= 1.1
        else:
            self.zoom_level /= 1.1

        # Limit zoom level
        self.zoom_level = max(0.05, min(self.zoom_level, 1.0))

        self.display_map()

    def calibrate_offset(self):
        def on_calibrate():
            nonlocal root
            self.offset_x = -root.winfo_x()
            self.offset_y = -root.winfo_y()
            self.offset_label.config(text=f"Current Offset: ({self.offset_x}, {self.offset_y})")
            root.quit()

        root = tk.Toplevel(self)
        root.title('Offset Calibrator')
        root.geometry("300x240+0+0")
        root.wm_attributes("-topmost", 1)

        ttk.Label(root, text="Move this window to the top-left corner\nof your primary monitor, then click 'Calibrate'.\n\nSnapping to the corner works.\nMaximize does NOT.", justify=tk.LEFT, padding=10).pack()

        ttk.Button(root, text="Calibrate", command=on_calibrate).pack(fill="both", expand=True, padx=20, pady=20)

        root.mainloop()
        root.destroy()

if __name__ == "__main__":
    app = AdvancedPlacementTool()
    app.mainloop()



# import tkinter as tk
# from tkinter import ttk, filedialog, messagebox
# import os
# import random
# import time
# import pyautogui
# import pygetwindow as gw
# import json
# from datetime import datetime
# from monitorinfoexhelper import get_monitors_info
# from wde_map_generator import generate_map, show_mouse_position
# from PIL import ImageTk, Image




# class EnhancedPlacementTool(tk.Tk):
#     def __init__(self):
#         super().__init__()
#         self.title("Enhanced Windows Placement Test Tool")
#         self.geometry("800x600")
        
#         self.desktop_info = None
#         self.create_gui()

#     def create_gui(self):
#         self.notebook = ttk.Notebook(self)
#         self.notebook.pack(fill=tk.BOTH, expand=True)

#         # Test tab
#         self.test_frame = ttk.Frame(self.notebook)
#         self.notebook.add(self.test_frame, text="Placement Test")
#         self.create_test_tab()

#         # Monitor Info tab
#         self.monitor_frame = ttk.Frame(self.notebook)
#         self.notebook.add(self.monitor_frame, text="Monitor Info")
#         self.create_monitor_tab()

#         # Map tab
#         self.map_frame = ttk.Frame(self.notebook)
#         self.notebook.add(self.map_frame, text="Desktop Map")
#         self.create_map_tab()

#     def create_test_tab(self):
#         # File selection
#         self.file_frame = ttk.LabelFrame(self.test_frame, text="File Selection")
#         self.file_frame.pack(fill=tk.X, padx=10, pady=5)

#         self.file_entry = ttk.Entry(self.file_frame, width=50)
#         self.file_entry.pack(side=tk.LEFT, padx=5, pady=5)

#         self.browse_button = ttk.Button(self.file_frame, text="Browse", command=self.browse_file)
#         self.browse_button.pack(side=tk.LEFT, padx=5, pady=5)

#         # Coordinates input
#         self.coord_frame = ttk.LabelFrame(self.test_frame, text="Coordinates")
#         self.coord_frame.pack(fill=tk.X, padx=10, pady=5)

#         ttk.Label(self.coord_frame, text="X:").grid(row=0, column=0, padx=5, pady=5)
#         self.x_entry = ttk.Entry(self.coord_frame, width=10)
#         self.x_entry.grid(row=0, column=1, padx=5, pady=5)

#         ttk.Label(self.coord_frame, text="Y:").grid(row=0, column=2, padx=5, pady=5)
#         self.y_entry = ttk.Entry(self.coord_frame, width=10)
#         self.y_entry.grid(row=0, column=3, padx=5, pady=5)

#         # Test button
#         self.test_button = ttk.Button(self.test_frame, text="Run Placement Test", command=self.run_placement_test)
#         self.test_button.pack(pady=10)

#         # Results
#         self.results_text = tk.Text(self.test_frame, wrap=tk.WORD, height=15)
#         self.results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

#     def create_monitor_tab(self):
#         self.monitor_text = tk.Text(self.monitor_frame, wrap=tk.WORD)
#         self.monitor_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

#         self.refresh_button = ttk.Button(self.monitor_frame, text="Refresh Monitor Info", command=self.refresh_monitor_info)
#         self.refresh_button.pack(pady=5)

#     def create_map_tab(self):
#         self.map_canvas = tk.Canvas(self.map_frame)
#         self.map_canvas.pack(fill=tk.BOTH, expand=True)

#         self.update_map_button = ttk.Button(self.map_frame, text="Update Map", command=self.update_map)
#         self.update_map_button.pack(pady=5)

#     def browse_file(self):
#         file_path = filedialog.askopenfilename()
#         if file_path:
#             self.file_entry.delete(0, tk.END)
#             self.file_entry.insert(0, file_path)

#     def run_placement_test(self):
#         file_path = self.file_entry.get()
#         try:
#             x = int(self.x_entry.get())
#             y = int(self.y_entry.get())
#         except ValueError:
#             messagebox.showerror("Invalid Input", "Please enter valid integer coordinates.")
#             return

#         if not os.path.exists(file_path):
#             messagebox.showerror("File Not Found", "The specified file does not exist.")
#             return

#         self.results_text.delete(1.0, tk.END)
#         self.results_text.insert(tk.END, f"Running placement test for file: {file_path}\n")
#         self.results_text.insert(tk.END, f"Requested coordinates: ({x}, {y})\n\n")

#         # Open the file
#         os.startfile(file_path)
#         time.sleep(2)  # Wait for the application to open

#         # Get the window
#         windows = gw.getWindowsWithTitle(os.path.basename(file_path))
#         if not windows:
#             self.results_text.insert(tk.END, "Error: Window not found.\n")
#             return

#         window = windows[0]

#         # Record initial position
#         initial_pos = window.left, window.top
#         self.results_text.insert(tk.END, f"Initial window position: {initial_pos}\n")

#         # Move the window
#         window.moveTo(x, y)
#         time.sleep(0.5)  # Wait for the move to complete

#         # Record new position
#         new_pos = window.left, window.top
#         self.results_text.insert(tk.END, f"New window position: {new_pos}\n")

#         # Calculate and display offset
#         offset_x = new_pos[0] - x
#         offset_y = new_pos[1] - y
#         self.results_text.insert(tk.END, f"Offset from requested position: ({offset_x}, {offset_y})\n")

#         # Get monitor information
#         monitor_info = self.get_monitor_info_for_position(x, y)
#         if monitor_info:
#             self.results_text.insert(tk.END, f"\nMonitor Information:\n{json.dumps(monitor_info, indent=2)}\n")
#         else:
#             self.results_text.insert(tk.END, "\nError: Could not determine monitor information for the given position.\n")

#     def get_monitor_info_for_position(self, x, y):
#         if not self.desktop_info:
#             self.refresh_monitor_info()
        
#         for monitor in self.desktop_info["monitors"]:
#             left, top, right, bottom = monitor["screen_coords"]
#             if left <= x < right and top <= y < bottom:
#                 return monitor
#         return None

#     def refresh_monitor_info(self):
#         self.desktop_info = {"monitors": get_monitors_info()}
#         self.monitor_text.delete(1.0, tk.END)
#         self.monitor_text.insert(tk.END, json.dumps(self.desktop_info, indent=4))
#         self.update_map()

#     def update_map(self):
#         if not self.desktop_info:
#             self.refresh_monitor_info()

#         map_image = generate_map(self.desktop_info, show_grid=True, show_numbers=True, show_legend=True, mark_origin=True)
#         map_image.thumbnail((700, 700), Image.LANCZOS)
#         self.map_photo = ImageTk.PhotoImage(map_image)
        
#         self.map_canvas.delete("all")
#         self.map_canvas.create_image(0, 0, anchor=tk.NW, image=self.map_photo)
        
#         # Start updating mouse position
#         self.update_mouse_position()

#     def update_mouse_position(self):
#         if self.desktop_info:
#             mouse_x, mouse_y = pyautogui.position()
#             map_image = generate_map(self.desktop_info, show_grid=True, show_numbers=True, show_legend=True, mark_origin=True)
#             map_with_mouse = show_mouse_position(map_image, mouse_x, mouse_y)
#             map_with_mouse.thumbnail((700, 700), Image.LANCZOS)
#             self.map_photo = ImageTk.PhotoImage(map_with_mouse)
            
#             self.map_canvas.delete("all")
#             self.map_canvas.create_image(0, 0, anchor=tk.NW, image=self.map_photo)
            
#             # Update mouse position text
#             self.map_canvas.delete("mouse_pos_text")
#             self.map_canvas.create_text(10, 10, anchor=tk.NW, text=f"Mouse: ({mouse_x}, {mouse_y})", tags="mouse_pos_text")
            
#         self.after(100, self.update_mouse_position)

# if __name__ == "__main__":
#     app = EnhancedPlacementTool()
#     app.mainloop()