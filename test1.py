# -*- coding: utf-8 -*-
"""
Created on Fri Jun 16 07:06:23 2024

@author: Thomas
"""

# ColorCatcher
# This standalone tool can be used to capture the color from underneath your mouse pointer

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import ImageGrab, ImageTk, Image, ImageDraw
import pyautogui
import threading
import time


class ColorCatcher:
    def __init__(self, root):
        self.capturing = False
        self.colors = []
        self.zoom_multiplier = tk.IntVar(value=4)
        self.stop_threads = False
        self.overlay = None

        self.root = root
        self.root.title("ColorCatcher")
        self.root.geometry("420x420")
        self.root.attributes("-topmost", True)

        self.setup_gui()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.stop_capture()
        self.root.destroy()

    def setup_gui(self):
        main_frame = ttk.Frame(self.root, padding=5)
        main_frame.pack(fill=tk.BOTH, expand=True)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.start_stop_button = ttk.Button(button_frame, text="Start", command=self.toggle_capture)
        self.start_stop_button.pack(side=tk.LEFT, padx=5)

        self.save_button = ttk.Button(button_frame, text="Save", command=self.save_colors)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.use_screenshot_var = tk.BooleanVar(value=False)
        self.use_screenshot_checkbox = ttk.Checkbutton(button_frame, text="Screenshot", variable=self.use_screenshot_var)
        self.use_screenshot_checkbox.pack(side=tk.RIGHT, padx=5)

        zoom_dropdown = ttk.Combobox(button_frame, textvariable=self.zoom_multiplier, values=list(range(1, 17)), width=2)
        zoom_dropdown.pack(side=tk.RIGHT, padx=5)
        zoom_dropdown.current(3)
        ttk.Label(button_frame, text="Zoom ratio:").pack(side=tk.RIGHT, padx=5)

        self.paned_window = ttk.Panedwindow(main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(self.paned_window, relief=tk.SUNKEN)
        left_frame.pack_propagate(False)
        self.paned_window.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Caught Colors:").pack(anchor=tk.CENTER, padx=5, pady=5)
        self.text_field = tk.Text(left_frame)
        self.text_field.pack(fill=tk.BOTH, expand=True)

        self.right_frame = ttk.Frame(self.paned_window, relief=tk.SUNKEN)
        self.right_frame.pack_propagate(False)
        self.paned_window.add(self.right_frame, weight=1)

        self.right_paned_window = ttk.Panedwindow(self.right_frame, orient=tk.VERTICAL)
        self.right_paned_window.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        zoomed_frame = ttk.Frame(self.right_paned_window, relief=tk.SUNKEN, borderwidth=0)
        zoomed_frame.pack_propagate(False)
        self.right_paned_window.add(zoomed_frame, weight=1)

        self.zoomed_canvas = tk.Canvas(zoomed_frame, bg='grey', highlightthickness=0)
        self.zoomed_canvas.pack(fill=tk.BOTH, expand=True)

        color_frame = ttk.Frame(self.right_paned_window, relief=tk.SUNKEN, borderwidth=0)
        color_frame.pack_propagate(False)
        self.right_paned_window.add(color_frame, weight=1)

        self.color_canvas = tk.Canvas(color_frame, bg='white', highlightthickness=0)
        self.color_canvas.pack(fill=tk.BOTH, expand=True)

        self.color_canvas.bind("<Configure>", self.on_color_canvas_resize)

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.root.update_idletasks()

        self.root.after(100, self.center_panes)

        self.root.bind('<Escape>', self.stop_capture)
        self.root.bind('<space>', self.stop_capture)

        print("GUI setup complete.")

    def center_panes(self):
        self.root.update_idletasks()
        self.paned_window.sashpos(0, self.root.winfo_width() // 2)
        self.right_paned_window.sashpos(0, self.right_frame.winfo_height() // 2)

    def toggle_capture(self):
        print("Toggling capture mode...")
        if self.capturing:
            self.stop_capture()
        else:
            self.stop_threads = False
            self.capturing = True
            self.start_stop_button.config(text="Stop")
            self.create_custom_cursor()
            self.root.config(cursor="crosshair")
            self.root.bind("<Button-1>", self.capture_color)
            self.color_canvas.delete("all")  # Remove placeholder when capturing starts

            if self.use_screenshot_var.get():
                self.fullscreen_screenshot()

            self.update_zoomed_view_thread()
            self.start_update_color_display_thread()
            self.draw_static_border()

    def stop_capture(self, event=None):
        print("Stopping capture mode...")
        self.stop_threads = True
        print(f"stop_threads set to {self.stop_threads}")
        self.capturing = False
        self.start_stop_button.config(text="Start")
        self.root.config(cursor="")
        self.root.unbind("<Button-1>")
        self.color_canvas.delete("all")
        self.color_canvas.create_image(0, 0, anchor=tk.NW, image=self.transparency_tk, tags="transparency")

        # Remove the full-screen overlay
        if self.overlay:
            self.overlay.destroy()
            self.overlay = None

        print("Active threads before joining:", threading.enumerate())

        try:
            if self.update_zoomed_thread and self.update_zoomed_thread.is_alive():
                print("Joining update_zoomed_thread")
                self.update_zoomed_thread.join(timeout=1)
                print("update_zoomed_thread joined")
        except AttributeError:
            pass

        try:
            if self.update_color_display_thread and self.update_color_display_thread.is_alive():
                print("Joining update_color_display_thread")
                self.update_color_display_thread.join(timeout=1)
                print("update_color_display_thread joined")
        except AttributeError:
            pass

        print("Active threads after joining:", threading.enumerate())

    def capture_color(self, event):
        print("Capturing color...")
        x, y = pyautogui.position()
        screenshot = pyautogui.screenshot()
        if 0 <= x < screenshot.width and 0 <= y < screenshot.height:
            rgb = screenshot.getpixel((x, y))
            color_hex = f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'

            self.colors.append(color_hex)
            self.text_field.insert(tk.END, f"{color_hex}\n")

            self.color_canvas.delete("transparency")
            self.color_canvas.create_rectangle(0, 0, self.color_canvas.winfo_width(), self.color_canvas.winfo_height(), fill=color_hex)
        else:
            print("Coordinates out of bounds for screenshot.")

    def save_colors(self):
        self.stop_capture()  # Stop capturing before saving
        print("Saving colors...")
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'w') as f:
                f.write("\n".join(self.colors))
            messagebox.showinfo("Save Successful", "Colors saved successfully!")

    def draw_static_border(self):
        self.zoomed_canvas.delete("overlay")
        zoom = self.zoom_multiplier.get()
        canvas_width = self.zoomed_canvas.winfo_width()
        canvas_height = self.zoomed_canvas.winfo_height()
        pixel_size = canvas_width // zoom

        center_x = canvas_width // 2
        center_y = canvas_height // 2

        border_x1 = center_x - pixel_size // 2
        border_y1 = center_y - pixel_size // 2
        border_x2 = center_x + pixel_size // 2
        border_y2 = center_y + pixel_size // 2

        self.zoomed_canvas.create_rectangle(
            border_x1, border_y1,
            border_x2, border_y2,
            outline="red", width=2, tags="overlay"
        )

    def update_zoomed_view(self):
        print("Starting update_zoomed_view thread")
        while True:
            if self.stop_threads:
                print("Exiting update_zoomed_view loop due to stop_threads")
                break
            print(f"Running update_zoomed_view loop, stop_threads={self.stop_threads}")
            x, y = pyautogui.position()
            zoom = self.zoom_multiplier.get()
            canvas_width = self.zoomed_canvas.winfo_width()
            canvas_height = self.zoomed_canvas.winfo_height()
            region_size = canvas_width // zoom

            im = pyautogui.screenshot(region=(x - region_size // 2, y - region_size // 2, region_size, region_size))
            zoomed_im = im.resize((canvas_width, canvas_height), Image.NEAREST)
            self.zoomed_im_tk = ImageTk.PhotoImage(zoomed_im)
            self.zoomed_canvas.create_image(0, 0, anchor=tk.NW, image=self.zoomed_im_tk)
            self.zoomed_canvas.config(scrollregion=self.zoomed_canvas.bbox(tk.ALL))
            time.sleep(0.1)
        print("Exiting update_zoomed_view thread")

    def update_zoomed_view_thread(self):
        if self.capturing:
            self.update_zoomed_thread = threading.Thread(target=self.update_zoomed_view)
            self.update_zoomed_thread.start()

    def update_color_display(self):
        print("Starting update_color_display thread")
        while True:
            if self.stop_threads:
                print("Exiting update_color_display loop due to stop_threads")
                break
            x, y = pyautogui.position()
            rgb = pyautogui.screenshot().getpixel((x, y))
            color_hex = f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
            self.color_canvas.delete("transparency")
            self.color_canvas.create_rectangle(0, 0, self.color_canvas.winfo_width(), self.color_canvas.winfo_height(), fill=color_hex)
            time.sleep(0.1)
        print("Exiting update_color_display thread")

    def start_update_color_display_thread(self):
        if self.capturing:
            self.update_color_display_thread = threading.Thread(target=self.update_color_display)
            self.update_color_display_thread.start()

    def on_color_canvas_resize(self, event):
        self.color_canvas.delete("transparency")
        width, height = event.width, event.height

        block_size = 20
        checkerboard = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(checkerboard)
        for y in range(0, height, block_size):
            for x in range(0, width, block_size):
                color = (69, 69, 69) if (x // block_size + y // block_size) % 2 == 0 else (255, 255, 255)
                draw.rectangle([x, y, x + block_size, y + block_size], fill=color)

        self.transparency_tk = ImageTk.PhotoImage(checkerboard)
        self.color_canvas.create_image(0, 0, anchor=tk.NW, image=self.transparency_tk, tags="transparency")

    def fullscreen_screenshot(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        screenshot = pyautogui.screenshot()
        self.screenshot_image = ImageTk.PhotoImage(screenshot)
        
        self.overlay = tk.Toplevel(self.root)
        self.overlay.geometry(f"{screen_width}x{screen_height}+0+0")
        self.overlay.attributes("-fullscreen", True)
        self.overlay.attributes("-topmost", True)
        self.overlay.overrideredirect(True)
        
        canvas = tk.Canvas(self.overlay, width=screen_width, height=screen_height)
        canvas.pack(fill=tk.BOTH, expand=True)
        canvas.create_image(0, 0, anchor=tk.NW, image=self.screenshot_image)
        
        self.root.after(100, self.lift_tool)

    def lift_tool(self):
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(200, self.lift_tool)

    def create_custom_cursor(self):
        cursor_size = 32
        cursor_image = tk.PhotoImage(width=cursor_size, height=cursor_size)
        cursor_image.put(("white",) * cursor_size, to=(0, 0, cursor_size, cursor_size))
        for i in range(cursor_size):
            cursor_image.put("black", to=(i, cursor_size // 2))
            cursor_image.put("black", to=(cursor_size // 2, i))
        for i in range(cursor_size // 2 - 1, cursor_size // 2 + 2):
            for j in range(cursor_size // 2 - 1, cursor_size // 2 + 2):
                cursor_image.put("white", to=(i, j))
        self.root.config(cursor="crosshair")


if __name__ == "__main__":
    root = tk.Tk()
    app = ColorCatcher(root)
    root.mainloop()
