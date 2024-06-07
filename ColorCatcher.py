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
from PIL import ImageGrab, ImageTk, Image
import pyautogui
import threading

class ColorCatcher:
    def __init__(self, root):
        self.capturing = False
        self.colors = []
        self.zoom_multiplier = tk.IntVar(value=4)

        self.root = root
        self.root.title("ColorCatcher")
        self.root.geometry("800x600")
        self.root.attributes("-topmost", True)

        self.setup_gui()

    def setup_gui(self):
        print("Setting up GUI...")
        
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        self.start_stop_button = ttk.Button(button_frame, text="Start", command=self.toggle_capture)
        self.start_stop_button.pack(side=tk.LEFT, padx=5)

        self.save_button = ttk.Button(button_frame, text="Save", command=self.save_colors)
        self.save_button.pack(side=tk.LEFT, padx=5)

        zoom_dropdown = ttk.Combobox(button_frame, textvariable=self.zoom_multiplier, values=list(range(1, 9)))
        zoom_dropdown.pack(side=tk.RIGHT, padx=5)
        zoom_dropdown.current(3)  # Default to 4x zoom
        ttk.Label(button_frame, text="Zoom ratio:").pack(side=tk.RIGHT, padx=5)

        paned_window = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # Left pane
        left_frame = ttk.Frame(paned_window, relief=tk.SUNKEN)
        paned_window.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Caught Colors:").pack(anchor=tk.W, padx=5, pady=5)
        self.text_field = tk.Text(left_frame, height=20, width=30)
        self.text_field.pack(fill=tk.BOTH, expand=True)

        # Right pane
        right_frame = ttk.Frame(paned_window, relief=tk.SUNKEN)
        paned_window.add(right_frame, weight=1)

        right_paned_window = ttk.Panedwindow(right_frame, orient=tk.VERTICAL)
        right_paned_window.pack(fill=tk.BOTH, expand=True)

        self.zoomed_canvas = tk.Canvas(right_paned_window, bg='grey')
        right_paned_window.add(self.zoomed_canvas, weight=1)

        self.color_display = tk.Label(right_paned_window, text="", bg="white", width=200, height=200)
        right_paned_window.add(self.color_display, weight=1)

        # Set initial sash positions
        self.root.update_idletasks()
        paned_window.sashpos(0, 400)
        right_paned_window.sashpos(0, 300)

        self.update_zoomed_view()
        print("GUI setup complete.")

    def toggle_capture(self):
        print("Toggling capture mode...")
        if self.capturing:
            self.capturing = False
            self.start_stop_button.config(text="Start")
            self.root.config(cursor="")
            self.root.unbind("<Button-1>")
        else:
            self.capturing = True
            self.start_stop_button.config(text="Stop")
            self.root.config(cursor="crosshair")
            self.root.bind("<Button-1>", self.capture_color)
            self.update_zoomed_view_thread()

    def capture_color(self, event):
        print("Capturing color...")
        x, y = pyautogui.position()
        rgb = pyautogui.screenshot().getpixel((x, y))
        color_hex = f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'

        self.colors.append(color_hex)
        self.text_field.insert(tk.END, f"{color_hex}\n")

        self.color_display.config(bg=color_hex)

    def save_colors(self):
        print("Saving colors...")
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'w') as f:
                f.write("\n".join(self.colors))
            messagebox.showinfo("Save Successful", "Colors saved successfully!")

    def update_zoomed_view(self):
        if self.capturing:
            x, y = pyautogui.position()
            zoom = self.zoom_multiplier.get()
            region_size = 100 // zoom
            im = pyautogui.screenshot(region=(x - region_size // 2, y - region_size // 2, region_size, region_size))
            zoomed_im = im.resize((200, 200), Image.NEAREST)
            self.zoomed_im_tk = ImageTk.PhotoImage(zoomed_im)
            self.zoomed_canvas.create_image(0, 0, anchor=tk.NW, image=self.zoomed_im_tk)
            self.zoomed_canvas.config(scrollregion=self.zoomed_canvas.bbox(tk.ALL))
            self.color_display.config(bg=f'#{im.getpixel((region_size//2, region_size//2))[0]:02x}{im.getpixel((region_size//2, region_size//2))[1]:02x}{im.getpixel((region_size//2, region_size//2))[2]:02x}')
        self.root.after(100, self.update_zoomed_view)

    def update_zoomed_view_thread(self):
        thread = threading.Thread(target=self.update_zoomed_view)
        thread.start()


if __name__ == "__main__":
    root = tk.Tk()
    app = ColorCatcher(root)
    root.mainloop()
