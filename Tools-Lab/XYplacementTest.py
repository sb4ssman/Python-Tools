# -*- coding: utf-8 -*-
"""
Created on Tue Jul 09 19:24:28 2024

@author: Thomas
"""





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
import threading

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

class AdvancedPlacementTool(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Advanced Windows Placement Test Tool")
        self.geometry("800x600")
        
        self.desktop_info = None
        self.offset_x, self.offset_y = 0, 0
        self.zoom_level = 1.0
        self.base_map = None
        self.map_photo = None
        self.tracking_active = False
        self.is_map_tab_active = False
        self.map_update_thread = None
        self.stop_thread = threading.Event()
        self.test_windows = []

        self.create_gui()
        # self.clear_monitor_info() # this will populate instructions
        
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

    def create_gui(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.monitor_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.monitor_frame, text="Monitor Info")
        self.create_monitor_tab()

        self.map_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.map_frame, text="Desktop Map")
        self.create_map_tab()

        self.calibration_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.calibration_frame, text="Offset Calibration")
        self.create_calibration_tab()

        self.test_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.test_frame, text="Placement Test")
        self.create_test_tab()




    def create_monitor_tab(self):
        self.monitor_text = tk.Text(self.monitor_frame, wrap=tk.WORD)
        self.monitor_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        button_frame = ttk.Frame(self.monitor_frame)
        button_frame.pack(pady=5)

        self.refresh_button = ttk.Button(button_frame, text="Refresh Monitor Info", command=self.refresh_monitor_info)
        self.refresh_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(button_frame, text="Clear", command=self.clear_monitor_info)
        self.clear_button.pack(side=tk.LEFT, padx=5)

    def display_instructions(self):
        instructions = """
        Application Instructions and Notes:

        1. This application helps test window placement across multiple monitors.
        2. Use the 'Refresh Monitor Info' button to get the latest monitor configuration.
        3. The 'Clear' button will reset all fields and display these instructions.

        Window Placement Process:
        - We use the `os.startfile()` function to launch a test application (Notepad).
        - Window placement is done using the `pygetwindow` library, which interacts with Windows APIs.
        - The `window.moveTo(x, y)` function call ultimately uses the Windows SetWindowPos function.

        Coordinate Systems:
        - The primary monitor's origin pixel (0, 0) is the "true origin" for the user.
        - Windows may have an offset between its coordinate system and the true origin.
        - Our goal is to detect this offset and accurately place windows on any monitor.
        - By comparing requested positions with actual window positions, we can calculate this offset.

        Remember: The Windows offset should be measured relative to the true origin (primary monitor's top-left corner).
        """
        self.monitor_text.insert(tk.END, instructions)

    def create_map_tab(self):
        # Configure style for black background
        style = ttk.Style()
        style.configure("Black.TFrame", background="black")
        
        # Create a frame with black background
        self.map_background_frame = ttk.Frame(self.map_frame, style="Black.TFrame")
        self.map_background_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Create the canvas with black background
        self.map_canvas = tk.Canvas(self.map_background_frame, bg="black", highlightthickness=0)
        self.map_canvas.pack(fill=tk.BOTH, expand=True)

        # Create a frame for the button with black background
        button_frame = ttk.Frame(self.map_frame, style="Black.TFrame")
        button_frame.pack(fill=tk.X, pady=5)

        # Configure style for the button
        style.configure("Black.TButton", background="black", foreground="white")
        self.update_map_button = ttk.Button(button_frame, text="Refresh Map", command=self.update_map, style="Black.TButton")
        self.update_map_button.pack()

        # Bind events
        self.map_canvas.bind("<ButtonPress-1>", self.start_pan)
        self.map_canvas.bind("<B1-Motion>", self.pan)
        self.map_canvas.bind("<Motion>", self.on_mouse_move)
        self.map_canvas.bind("<MouseWheel>", self.zoom_map)

        # Ensure the map frame uses the black background
        self.map_frame.config(style="Black.TFrame")

    def create_calibration_tab(self):
        ttk.Label(self.calibration_frame, text="Offset Calibration", font=("", 16)).pack(pady=10)
        ttk.Label(self.calibration_frame, text="Click 'Calibrate' to detect the offset between\nWindows virtual desktop origin and primary monitor origin.").pack()
        
        self.calibrate_button = ttk.Button(self.calibration_frame, text="Calibrate", command=self.calibrate_offset)
        self.calibrate_button.pack(pady=20)

        self.calibration_offset_label = ttk.Label(self.calibration_frame, text="Current Offset: Not Calibrated")
        self.calibration_offset_label.pack()

        ttk.Label(self.calibration_frame, text="Manual Offset Entry:").pack(pady=(20, 5))
        
        offset_frame = ttk.Frame(self.calibration_frame)
        offset_frame.pack()

        ttk.Label(offset_frame, text="X:").grid(row=0, column=0, padx=5)
        self.offset_x_entry = ttk.Entry(offset_frame, width=10)
        self.offset_x_entry.grid(row=0, column=1, padx=5)

        ttk.Label(offset_frame, text="Y:").grid(row=0, column=2, padx=5)
        self.offset_y_entry = ttk.Entry(offset_frame, width=10)
        self.offset_y_entry.grid(row=0, column=3, padx=5)

        self.apply_manual_offset_button = ttk.Button(self.calibration_frame, text="Apply Manual Offset", command=self.apply_manual_offset)
        self.apply_manual_offset_button.pack(pady=10)


    def create_test_tab(self):
        top_frame = ttk.Frame(self.test_frame)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        self.monitor_select_frame = ttk.LabelFrame(top_frame, text="Select Monitor")
        self.monitor_select_frame.pack(side=tk.LEFT, padx=(0, 5))

        self.monitor_var = tk.StringVar()
        self.monitor_dropdown = ttk.Combobox(self.monitor_select_frame, textvariable=self.monitor_var, state="readonly")
        self.monitor_dropdown.pack(pady=5)
        self.monitor_dropdown.bind("<<ComboboxSelected>>", self.update_monitor_info)

        self.offset_label = ttk.Label(top_frame, text="Current Offset: Not Calibrated")
        self.offset_label.pack(side=tk.LEFT, padx=(5, 0), pady=10)

        info_frame = ttk.Frame(self.test_frame)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        self.monitor_info_frame = ttk.LabelFrame(info_frame, text="Monitor Information")
        self.monitor_info_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))

        self.monitor_info_grid = ttk.Frame(self.monitor_info_frame)
        self.monitor_info_grid.pack(padx=5, pady=5)

        self.raw_coord_frame = ttk.LabelFrame(info_frame, text="Raw Coordinates")
        self.raw_coord_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        self.raw_coord_grid = ttk.Frame(self.raw_coord_frame)
        self.raw_coord_grid.pack(padx=5, pady=5)

        self.adjusted_coord_frame = ttk.LabelFrame(info_frame, text="Adjusted Coordinates")
        self.adjusted_coord_frame.pack(side=tk.LEFT, fill=tk.BOTH)

        self.adjusted_coord_grid = ttk.Frame(self.adjusted_coord_frame)
        self.adjusted_coord_grid.pack(padx=5, pady=5)

        bottom_frame = ttk.Frame(self.test_frame)
        bottom_frame.pack(fill=tk.X, padx=10, pady=5)

        self.test_options_frame = ttk.LabelFrame(bottom_frame, text="Test Options")
        self.test_options_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))

        self.use_offset_var = tk.BooleanVar(value=False)
        self.use_offset_radio = ttk.Radiobutton(self.test_options_frame, text="Use Raw Coordinates", variable=self.use_offset_var, value=False, command=self.update_calculated_coordinates)
        self.use_offset_radio.pack(anchor="nw", pady=2)
        self.use_offset_radio_adjusted = ttk.Radiobutton(self.test_options_frame, text="Use Offset-Adjusted Coordinates", variable=self.use_offset_var, value=True, command=self.update_calculated_coordinates)
        self.use_offset_radio_adjusted.pack(anchor="sw", pady=2)

        self.test_button = ttk.Button(bottom_frame, text="Run Placement Tests", command=self.run_placement_tests)
        self.test_button.pack(side=tk.LEFT, padx=5)

        self.close_windows_button = ttk.Button(bottom_frame, text="Close Test Windows", command=self.close_test_windows)
        self.close_windows_button.pack(side=tk.LEFT, padx=5)

        self.results_text = tk.Text(self.test_frame, wrap=tk.WORD, height=20)
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)





# Test defs and functions
###################################

    def on_closing(self):
        self.stop_thread.set()
        if self.map_update_thread and self.map_update_thread.is_alive():
            self.map_update_thread.join()
        self.destroy()

    def on_tab_change(self, event):
        selected_tab = event.widget.select()
        tab_text = event.widget.tab(selected_tab, "text")
        
        if tab_text == "Desktop Map":
            self.is_map_tab_active = True
            self.update_map()
            self.start_crosshair_tracking()
        else:
            self.is_map_tab_active = False
            self.stop_crosshair_tracking()

    def clear_monitor_info(self):
        self.monitor_text.delete(1.0, tk.END)
        self.desktop_info = None
        self.update_monitor_dropdown()
        self.display_instructions()


    def calibrate_offset(self):
        def on_calibrate():
            nonlocal root
            self.offset_x = -root.winfo_x()
            self.offset_y = -root.winfo_y()
            self.calibration_offset_label.config(text=f"Current Offset: ({self.offset_x}, {self.offset_y})")
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

    def apply_manual_offset(self):
        try:
            self.offset_x = int(self.offset_x_entry.get())
            self.offset_y = int(self.offset_y_entry.get())
            self.calibration_offset_label.config(text=f"Current Offset: ({self.offset_x}, {self.offset_y})")
            self.offset_label.config(text=f"Current Offset: ({self.offset_x}, {self.offset_y})")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid integer values for the offset.")
            


        

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
        self.update_monitor_dropdown()
        self.update_map()
    
    def update_monitor_dropdown(self):
        monitor_names = [f"Monitor {i+1}: {m['device_name']}" for i, m in enumerate(self.desktop_info['monitors'])]
        self.monitor_dropdown['values'] = monitor_names
        if monitor_names:
            self.monitor_dropdown.current(0)
            self.update_monitor_info()

    def update_monitor_info(self, event=None):
        selected_index = self.monitor_dropdown.current()
        if selected_index >= 0:
            monitor = self.desktop_info['monitors'][selected_index]
            
            for widget in self.monitor_info_grid.winfo_children():
                widget.destroy()

            info = [
                ("Device Name", monitor['device_name']),
                ("Resolution", f"{monitor['screen_coords'][2] - monitor['screen_coords'][0]}x{monitor['screen_coords'][3] - monitor['screen_coords'][1]}"),
                ("Position", f"({monitor['screen_coords'][0]}, {monitor['screen_coords'][1]})"),
                ("Is Primary", "Yes" if monitor.get('is_primary', False) else "No"),
                ("Taskbar Position", f"({monitor['taskbar_position'][0]}, {monitor['taskbar_position'][1]}, {monitor['taskbar_position'][2]}, {monitor['taskbar_position'][3]})")
            ]

            for i, (key, value) in enumerate(info):
                ttk.Label(self.monitor_info_grid, text=key + ":").grid(row=i, column=0, sticky="e", padx=5, pady=2)
                ttk.Label(self.monitor_info_grid, text=str(value)).grid(row=i, column=1, sticky="w", padx=5, pady=2)

            self.update_calculated_coordinates()

    def update_calculated_coordinates(self):
        selected_index = self.monitor_dropdown.current()
        if selected_index >= 0:
            monitor = self.desktop_info['monitors'][selected_index]
            window_size = (300, 300)

            raw_positions = self.calculate_corner_positions(monitor, window_size, False)
            adjusted_positions = self.calculate_corner_positions(monitor, window_size, True)

            for widget in self.raw_coord_grid.winfo_children():
                widget.destroy()
            for widget in self.adjusted_coord_grid.winfo_children():
                widget.destroy()

            for i, ((raw_pos, description), (adjusted_pos, _)) in enumerate(zip(raw_positions, adjusted_positions)):
                ttk.Label(self.raw_coord_grid, text=f"{description}:").grid(row=i, column=0, sticky="e", padx=5, pady=2)
                ttk.Label(self.raw_coord_grid, text=f"({raw_pos[0]}, {raw_pos[1]})").grid(row=i, column=1, sticky="w", padx=5, pady=2)

                ttk.Label(self.adjusted_coord_grid, text=f"{description}:").grid(row=i, column=0, sticky="e", padx=5, pady=2)
                ttk.Label(self.adjusted_coord_grid, text=f"({adjusted_pos[0]}, {adjusted_pos[1]})").grid(row=i, column=1, sticky="w", padx=5, pady=2)



    def calculate_corner_positions(self, monitor, window_size, use_offset):
        x1, y1, x2, y2 = monitor["screen_coords"]
        tx1, ty1, tx2, ty2 = monitor["taskbar_position"]
        w, h = window_size

        # Calculate usable area considering taskbar position
        usable_x1, usable_y1 = x1, y1
        usable_x2, usable_y2 = x2, y2

        if tx1 == x1 and tx2 != x2:  # Left taskbar
            usable_x1 = tx2
        elif ty1 == y1 and ty2 != y2:  # Top taskbar
            usable_y1 = ty2
        elif tx2 == x2 and tx1 != x1:  # Right taskbar
            usable_x2 = tx1
        elif ty2 == y2 and ty1 != y1:  # Bottom taskbar
            usable_y2 = ty1

        # Calculate corner positions within the usable area
        positions = [
            ((usable_x1, usable_y1), "Top-Left"),
            ((usable_x2 - w, usable_y1), "Top-Right"),
            ((usable_x1, usable_y2 - h), "Bottom-Left"),
            ((usable_x2 - w, usable_y2 - h), "Bottom-Right")
        ]

        if use_offset:
            positions = [((x + self.offset_x, y + self.offset_y), desc) for (x, y), desc in positions]

        return positions


# The map
#########################

    def update_map(self):
        if not self.desktop_info:
            self.refresh_monitor_info()
        elif self.is_map_tab_active:
            self.generate_and_display_map()

    def generate_and_display_map(self):
        self.base_map = generate_map(self.desktop_info, show_grid=True, show_numbers=True, show_legend=True, mark_origin=True)
        if not hasattr(self, 'initial_zoom_set'):
            self.fit_map_to_window()
            self.initial_zoom_set = True
        self.display_map()

    def fit_map_to_window(self):
        canvas_width = self.map_canvas.winfo_width()
        canvas_height = self.map_canvas.winfo_height()
        zoom_x = canvas_width / self.base_map.width
        zoom_y = canvas_height / self.base_map.height
        self.zoom_level = min(zoom_x, zoom_y, 1.0)
        
    def display_map(self, center_x=None, center_y=None):
        if self.base_map:
            zoomed_size = (
                int(self.base_map.width * self.zoom_level),
                int(self.base_map.height * self.zoom_level)
            )
            zoomed_map = self.base_map.copy()
            zoomed_map = zoomed_map.resize(zoomed_size, Image.LANCZOS)

            self.map_photo = ImageTk.PhotoImage(zoomed_map)
            self.map_canvas.delete("all")
            self.map_canvas.create_image(0, 0, anchor="nw", image=self.map_photo)

            if center_x is not None and center_y is not None:
                self.map_canvas.scan_dragto(
                    int(center_x * (1 - self.zoom_level)),
                    int(center_y * (1 - self.zoom_level)),
                    gain=1
                )

    def on_mouse_move(self, event):
        if self.base_map and self.tracking_active:
            screen_x, screen_y = pyautogui.position()
            self.update_crosshair(screen_x, screen_y)

    def update_crosshair(self, screen_x, screen_y):
        if not self.tracking_active:
            return

        if self.map_photo:
            self.map_canvas.delete("crosshair")
            self.map_canvas.delete("mouse_pos_text")
            
            # Calculate the position on the map
            map_x = screen_x * self.zoom_level
            map_y = screen_y * self.zoom_level
            
            # Draw crosshair
            self.map_canvas.create_line(map_x, 0, map_x, self.map_canvas.winfo_height(), fill="red", tags="crosshair")
            self.map_canvas.create_line(0, map_y, self.map_canvas.winfo_width(), map_y, fill="red", tags="crosshair")
            
            # Show mouse positions
            self.map_canvas.create_text(10, 10, anchor="nw", text=f"Screen: ({screen_x}, {screen_y})", tags="mouse_pos_text", fill="white")
            self.map_canvas.create_text(10, 30, anchor="nw", text=f"Map: ({int(map_x/self.zoom_level)}, {int(map_y/self.zoom_level)})", tags="mouse_pos_text", fill="white")

    def start_crosshair_tracking(self):
        if not self.tracking_active:
            self.tracking_active = True
            self.update_mouse_position()

    def stop_crosshair_tracking(self):
        self.tracking_active = False
        if self.map_photo:
            self.map_canvas.delete("crosshair")
            self.map_canvas.delete("mouse_pos_text")

    def update_mouse_position(self):
        if self.tracking_active:
            screen_x, screen_y = pyautogui.position()
            self.update_crosshair(screen_x, screen_y)
            self.after(50, self.update_mouse_position)

    def update_map_canvas(self, canvas_x, canvas_y, map_x, map_y, screen_x, screen_y):
        if self.map_photo:
            self.map_canvas.delete("crosshair")
            self.map_canvas.delete("mouse_pos_text")
            
            # Draw crosshair at the actual screen position on the map
            map_screen_x = (screen_x - self.desktop_info['monitors'][0]['screen_coords'][0]) * self.zoom_level
            map_screen_y = (screen_y - self.desktop_info['monitors'][0]['screen_coords'][1]) * self.zoom_level
            
            self.map_canvas.create_line(map_screen_x, 0, map_screen_x, self.map_canvas.winfo_height(), fill="red", tags="crosshair")
            self.map_canvas.create_line(0, map_screen_y, self.map_canvas.winfo_width(), map_screen_y, fill="red", tags="crosshair")
            
            # Show mouse positions
            self.map_canvas.create_text(10, 10, anchor="nw", text=f"Map: ({map_x}, {map_y})", tags="mouse_pos_text", fill="white")
            self.map_canvas.create_text(10, 30, anchor="nw", text=f"Screen: ({screen_x}, {screen_y})", tags="mouse_pos_text", fill="white")

    def zoom_map(self, event):
        if self.base_map:
            x = self.map_canvas.canvasx(event.x)
            y = self.map_canvas.canvasy(event.y)
            if event.delta > 0:
                self.zoom_level *= 1.1
            else:
                self.zoom_level /= 1.1
            self.zoom_level = max(0.1, min(self.zoom_level, 5.0))
            self.display_map(x, y)

    def start_pan(self, event):
        self.map_canvas.scan_mark(event.x, event.y)

    def pan(self, event):
        self.map_canvas.scan_dragto(event.x, event.y, gain=1)

# TEST FUNCTIONS
#######################



    def run_placement_tests(self):
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Running placement tests...\n\n")

            selected_index = self.monitor_dropdown.current()
            if selected_index < 0:
                self.results_text.insert(tk.END, "Error: No monitor selected.\n")
                return

            monitor = self.desktop_info['monitors'][selected_index]
            use_offset = self.use_offset_var.get()

            window_size = (self.window_measure, self.window_measure)
            positions = self.calculate_corner_positions(monitor, window_size, use_offset)

            for i, (pos, description) in enumerate(positions):
                self.results_text.insert(tk.END, f"Testing Position {i+1}: {description}\n")
                self.results_text.insert(tk.END, f"Requested position: {pos}\n")
                
                self.test_window_placement(pos, window_size, description)
                self.results_text.insert(tk.END, "\n")

            self.results_text.insert(tk.END, "All tests completed. Test windows left open for inspection.\n")



    def test_window_placement(self, pos, size, description):
        x, y = pos
        w, h = size

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as temp_file:
            temp_file.write(f"This test window has dimensions {w}x{h} and is placed at {x},{y} coords in the {description} corner of the usable area")
            temp_file_path = temp_file.name

        try:
            os.startfile(temp_file_path)
            time.sleep(1)  # Wait for the application to open

            windows = gw.getWindowsWithTitle(os.path.basename(temp_file_path))
            if not windows:
                self.results_text.insert(tk.END, "Error: Window not found.\n")
                return

            window = windows[0]

            window.moveTo(x, y)
            window.resizeTo(w, h)
            time.sleep(0.5)  # Wait for the move to complete

            new_pos = window.left, window.top
            new_size = window.width, window.height
            self.results_text.insert(tk.END, f"Actual window position: {new_pos}\n")
            self.results_text.insert(tk.END, f"Actual window size: {new_size}\n")

            offset_x = new_pos[0] - x
            offset_y = new_pos[1] - y
            self.results_text.insert(tk.END, f"Offset from requested position: ({offset_x}, {offset_y})\n")

            self.test_windows.append(window)

        except Exception as e:
            self.results_text.insert(tk.END, f"Error placing window: {str(e)}\n")
        finally:
            os.unlink(temp_file_path)


    def close_test_windows(self):
        for window in self.test_windows:
            try:
                window.close()
            except:
                pass  # Window might already be closed
        self.test_windows.clear()
        self.results_text.insert(tk.END, "All test windows closed.\n")




if __name__ == "__main__":
    app = AdvancedPlacementTool()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

