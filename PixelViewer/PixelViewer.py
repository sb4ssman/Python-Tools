# -*- coding: utf-8 -*-
"""
Created on Tue Jul 9 16:35:11 2024

@author: Thomas
"""

VERSION = "0.1.0"

# PixelViewer.py
# Provides a straight multiplication zoomed view for pixel magnification
# around a critical pixel, including dynamic targets.
# This tool does all the heavy lifting of:

# PixelViewer User Guide

# Quick Start:
# from PixelViewer import PixelViewer
# import tkinter as tk

# root = tk.Tk()
# frame = tk.Frame(root)
# frame.pack(fill=tk.BOTH, expand=True)

# pixel_viewer = PixelViewer(frame)
# pixel_viewer.start_viewer()

# root.mainloop()

# PixelViewer Parameters:
# - parent: tk.Frame - The Tkinter frame to contain the PixelViewer
# - multiplier: int = 16 - Zoom level
# - target: Callable[[], Tuple[int, int]] = None - Function returning (x, y) coordinates to focus on
# - crosshair: str = None - Crosshair type ("None", "pixel", "cross", "plus", "box", "thiccbox", "boxhair", "boxhair_2", "special", "special_2", "special_3")
# - color: str = "#ff0000" - Crosshair color
# - opacity: float = 1.0 - Crosshair opacity
# - invert_crosshair: bool = False - Invert colors under the crosshair
# - texture: str = "check_1" - Background texture ("None", "check_1", "check_2")
# - show_texture_on_stop: bool = False - Show texture when viewer is stopped
# - event_callback: Optional[Callable] = None - Callback function for update events
# - frame_rate: int = 60 - Frame rate for updates
# - debug_mode: bool = False - Enable debug mode for performance logging and frame saving

# Key Methods:
# - start_viewer(): Start the viewer
# - stop_viewer(): Stop the viewer
# - set_multiplier(multiplier: int): Set zoom level
# - set_target(target: Callable[[], Tuple[int, int]]): Set custom target function
# - set_crosshair(crosshair: str): Set crosshair type
# - set_crosshair_color(color: str): Set crosshair color
# - set_crosshair_opacity(opacity: float): Set crosshair opacity
# - set_invert_crosshair(invert: bool): Set crosshair inversion
# - set_texture(texture: str): Set background texture
# - set_show_texture_on_stop(show_texture_on_stop: bool): Set texture visibility on stop

# Connecting UI Controls:
# def on_zoom_change(value):
# pixel_viewer.set_multiplier(int(value))

# zoom_slider = tk.Scale(root, from_=1, to=32, orient=tk.HORIZONTAL, command=on_zoom_change)
# zoom_slider.pack()

# def on_start_stop():
# if pixel_viewer.viewer_thread and pixel_viewer.viewer_thread.is_alive():
# pixel_viewer.stop_viewer()
# start_stop_button.config(text="Start Viewer")
# else:
# pixel_viewer.start_viewer()
# start_stop_button.config(text="Stop Viewer")

# start_stop_button = tk.Button(root, text="Start Viewer", command=on_start_stop)
# start_stop_button.pack()

# # Similar patterns can be used for other controls (crosshair type, color, etc.)



import time
import os
from datetime import datetime

import threading
import time
from typing import Tuple, Callable, Optional
import tkinter as tk
from tkinter import ttk
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageChops
import mss
import queue
import pyautogui
import win32gui



###################
#                 #
#   PixelViewer   #
#                 #
###################


class PixelViewer:
    def __init__(self, parent: tk.Frame, # size: Tuple[int, int] = (208, 208), # Size can be anything: an odd multiple of the default multiplier is a good baseline
                 multiplier: int = 16, 
                 target: Callable[[], Tuple[int, int]] = None, # Can pass dynamic variables
                 crosshair: str = None, # crosshair_options = ["None", "boxhair", "cross", "pixel", "box", "special"]
                 color: str = "#ff0000", 
                 opacity: float = 1.0, 
                 invert_crosshair: bool = False,
                 texture: str = "check_1",  # Changed to texture with options None, check_1, check_2
                 show_texture_on_stop: bool = False,
                 event_callback: Optional[Callable] = None, 
                 frame_rate: int = 60,
                 debug_mode: bool = False):

        self.parent = parent
        self.is_running = False
        self.multiplier = multiplier
        self.target = target or (lambda: pyautogui.position())
        self.crosshair = crosshair
        self.color = color
        self.opacity = opacity
        self.invert_crosshair = invert_crosshair
        self.texture = texture
        self.show_texture_on_stop = show_texture_on_stop
        self.event_callback = event_callback
        self.frame_rate = frame_rate
        self.frame_interval = 1.0 / self.frame_rate
        self.last_update_time = 0

        self.current_image = None
        self.current_photo = None

        self.image_queue = queue.Queue(maxsize=1)
        self.processing_thread = None
        self.stop_processing = threading.Event()

        self.viewer_thread = None
        self.stop_thread = threading.Event()
        self.update_queue = queue.Queue()

        # Debug
        self.debug_mode = debug_mode
        self.frame_times = []
        self.last_fps_print = 0
        self.frame_count = 0


        self.setup_ui()
        self.parent.after(100, self.update_texture)  # Schedule texture update after a short delay

    def log_performance(self, start_time):
        frame_time = time.time() - start_time
        self.frame_times.append(frame_time)
        
        if len(self.frame_times) > 100:
            self.frame_times.pop(0)
        
        current_time = time.time()
        if current_time - self.last_fps_print >= 5:  # Print FPS every 5 seconds
            avg_frame_time = sum(self.frame_times) / len(self.frame_times)
            fps = 1 / avg_frame_time if avg_frame_time > 0 else 0
            print(f"FPS: {fps:.2f}, Avg Frame Time: {avg_frame_time*1000:.2f}ms")
            self.last_fps_print = current_time

    def setup_ui(self):
        self.canvas = tk.Canvas(self.parent)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.viewer_image = None
        self.canvas.bind('<Configure>', self.on_canvas_resize)

    def on_canvas_resize(self, event):
        if not self.is_running:
            self.update_texture()
        else:
            x, y = self.target()  # Get the current target position
            self.update_zoomed_view(x, y)
            
    def start_viewer(self):
        if self.viewer_thread is None or not self.viewer_thread.is_alive():
            self.stop_thread.clear()
            self.stop_processing.clear()
            self.viewer_thread = threading.Thread(target=self.update_viewer_thread)
            self.processing_thread = threading.Thread(target=self.process_image_thread)
            self.viewer_thread.daemon = True
            self.processing_thread.daemon = True
            self.viewer_thread.start()
            self.processing_thread.start()
            self.parent.after(10, self.update_canvas)
        self.canvas.itemconfigure("texture", state="hidden")
        self.is_running = True

    def stop_viewer(self):
        if self.viewer_thread and self.viewer_thread.is_alive():
            self.stop_thread.set()
            self.stop_processing.set()
            self.viewer_thread.join(timeout=2)
            self.processing_thread.join(timeout=2)
            self.viewer_thread = None
            self.processing_thread = None
        self.canvas.delete("viewer_image")
        self.canvas.delete("crosshair")
        if self.show_texture_on_stop and self.texture:
            self.update_texture()
            self.canvas.itemconfigure("texture", state="normal")
            self.canvas.tag_raise("texture")  # Ensure texture is on top
        else:
            self.canvas.itemconfigure("texture", state="hidden")
        self.is_running = False

    def update_viewer_thread(self):
        while not self.stop_thread.is_set():
            try:
                x, y = self.target()
                self.capture_and_process(x, y)
            except Exception as e:
                print(f"Error in viewer update: {e}")
            time.sleep(1 / self.frame_rate)

    def capture_and_process(self, x, y):
        zoom = max(1, int(self.multiplier))
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        region_width = (canvas_width // zoom) | 1
        region_height = (canvas_height // zoom) | 1

        region_x = x - region_width // 2
        region_y = y - region_height // 2

        with mss.mss() as sct:
            monitor = {"top": region_y, "left": region_x, "width": region_width, "height": region_height}
            screenshot = sct.grab(monitor)
            
            # Convert the raw BGR data to RGB
            im_array = np.array(screenshot, dtype=np.uint8)
            im_array = im_array[:, :, :3]  # Remove alpha channel if present
            im_array = im_array[:, :, ::-1]  # Flip BGR to RGB

        zoomed_array = np.repeat(np.repeat(im_array, zoom, axis=0), zoom, axis=1)

        try:
            self.image_queue.put_nowait((zoomed_array, self.crosshair, self.color))
        except queue.Full:
            pass  # Skip this frame if the queue is full

        if self.debug_mode:
            center_pixel = im_array[im_array.shape[0]//2, im_array.shape[1]//2]
            print(f"Center pixel RGB: {center_pixel}")
            
    def process_image_thread(self):
        while not self.stop_processing.is_set():
            try:
                zoomed_array, crosshair, color = self.image_queue.get(timeout=0.1)
                zoomed_im = Image.fromarray(zoomed_array, mode='RGB')
                if crosshair and crosshair != "None":
                    zoomed_im = self.apply_crosshair(zoomed_im)
                
                photo = ImageTk.PhotoImage(zoomed_im)
                self.parent.after_idle(self.update_canvas_image, photo)
            except queue.Empty:
                continue

    def process_queue(self):
        try:
            x, y, screenshot = self.update_queue.get_nowait()
            self.update_zoomed_view(x, y, screenshot)
        except queue.Empty:
            pass
        finally:
            if not self.stop_thread.is_set():
                self.parent.after(10, self.process_queue)

    def update_canvas_image(self, photo):
        if not hasattr(self, 'image_on_canvas'):
            self.image_on_canvas = self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        else:
            self.canvas.itemconfig(self.image_on_canvas, image=photo)
        self.current_photo = photo  # Keep a reference to avoid garbage collection

    def update_canvas(self):
        if not self.stop_thread.is_set():
            self.parent.after(10, self.update_canvas)

    def update_zoomed_view(self, x, y):
        if self.is_running:
            try:
                zoom = max(1, int(self.multiplier))
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()

                region_width = (canvas_width // zoom) | 1
                region_height = (canvas_height // zoom) | 1

                region_x = x - region_width // 2
                region_y = y - region_height // 2

                with mss.mss() as sct:
                    monitor = {"top": region_y, "left": region_x, "width": region_width, "height": region_height}
                    screenshot = sct.grab(monitor)
                    im_array = np.array(screenshot)

                zoomed_width = region_width * zoom
                zoomed_height = region_height * zoom
                
                # Use numpy for faster resizing
                zoomed_array = np.repeat(np.repeat(im_array, zoom, axis=0), zoom, axis=1)

                if self.crosshair and self.crosshair != "None":
                    zoomed_im = Image.fromarray(zoomed_array)
                    zoomed_im = self.apply_crosshair(zoomed_im)
                    zoomed_array = np.array(zoomed_im)

                # Update the current image only if it has changed
                if self.current_image is None or not np.array_equal(self.current_image, zoomed_array):
                    self.current_image = zoomed_array
                    self.current_photo = ImageTk.PhotoImage(Image.fromarray(zoomed_array))
                    
                    if not hasattr(self, 'image_on_canvas'):
                        self.image_on_canvas = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_photo)
                    else:
                        self.canvas.itemconfig(self.image_on_canvas, image=self.current_photo)

                if self.debug_mode and self.frame_count % 100 == 0:
                    self.save_debug_frame(Image.fromarray(zoomed_array))

                if self.event_callback:
                    self.event_callback({"type": "update", "image": Image.fromarray(zoomed_array)})

            except Exception as e:
                print(f"Error in update_zoomed_view: {e}")
                import traceback
                traceback.print_exc()

    def save_debug_frame(self, image):
        debug_dir = "debug_frames"
        os.makedirs(debug_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{debug_dir}/frame_{timestamp}_{self.frame_count}.png"
        image.save(filename)
        print(f"Saved debug frame: {filename}")

    def apply_crosshair(self, image):
        crosshair_im = Image.new('RGBA', image.size, (0, 0, 0, 0))
        center_x, center_y = image.width // 2, image.height // 2
        
        if self.crosshair == "special_2":
            self.draw_special_crosshair_2(crosshair_im, (center_x, center_y), image.width, image.height, self.color, self.multiplier)
        elif self.crosshair == "special_3":
            self.draw_special_crosshair_3(crosshair_im, (center_x, center_y), image.width, image.height, self.color, self.multiplier)
        else:
            self.draw_crosshair(crosshair_im, (center_x, center_y), image.width, image.height, self.color)

        if self.invert_crosshair:
            # Enforce full opacity for inversion
            return self.invert_crosshair_area(image, crosshair_im)
        else:
            if self.opacity < 1.0:
                crosshair_data = list(crosshair_im.split())
                crosshair_data[3] = crosshair_data[3].point(lambda x: int(x * self.opacity))
                crosshair_im = Image.merge('RGBA', crosshair_data)
            return Image.alpha_composite(image.convert('RGBA'), crosshair_im)

    def invert_crosshair_area(self, image, crosshair_image):
        # Create a binary mask from the crosshair image
        mask = crosshair_image.split()[3].point(lambda x: 255 if x > 0 else 0)
        
        # Invert the colors of the original image
        inverted = ImageChops.invert(image.convert('RGB'))
        
        # Use the mask to composite the inverted area onto the original image
        return Image.composite(inverted, image.convert('RGB'), mask)


    def draw_crosshair(self, image, center, width, height, color):
        draw = ImageDraw.Draw(image)
        center_x, center_y = center
        zoom = self.multiplier

        left_edge = center_x - zoom // 2
        right_edge = left_edge + zoom - 1
        top_edge = center_y - zoom // 2
        bottom_edge = top_edge + zoom - 1

        left = left_edge - 1
        right = right_edge + 1
        top = top_edge - 1
        bottom = bottom_edge + 1
        
        if self.crosshair == 'pixel':
            draw.point((center_x, center_y), fill=color)
        elif self.crosshair == 'cross':
            draw.line([center_x, 0, center_x, height], fill=color)
            draw.line([0, center_y, width, center_y], fill=color)
        elif self.crosshair == 'plus':
            segment_length = max(zoom * 2, 10)
            draw.line([center_x - segment_length, center_y, center_x + segment_length, center_y], fill=color)
            draw.line([center_x, center_y - segment_length, center_x, center_y + segment_length], fill=color)
        elif self.crosshair == 'box':
            draw.rectangle([left, top, right, bottom], outline=color)
        elif self.crosshair == 'thiccbox':
            for i in range(5):
                draw.rectangle([left-i, top-i, right+i, bottom+i], outline=color)
        elif self.crosshair == 'boxhair':
            draw.rectangle([left, top, right, bottom], outline=color)
            draw.line([center_x, 0, center_x, top], fill=color)
            draw.line([center_x, bottom, center_x, height], fill=color)
            draw.line([0, center_y, left, center_y], fill=color)
            draw.line([right, center_y, width, center_y], fill=color)
        elif self.crosshair == 'boxhair_2':
            draw.line([left, 0, left, height], fill=color)
            draw.line([right, 0, right, height], fill=color)
            draw.line([0, top, width, top], fill=color)
            draw.line([0, bottom, width, bottom], fill=color)
        elif self.crosshair == 'special':
            self.draw_special_crosshair(draw, (center_x, center_y), width, height, color)

        return image

    # Special crosshair - no scaling
    def draw_special_crosshair(self, draw, center, width, height, color):
        center_x, center_y = center
        
        triangle_base = 13
        triangle_height = 20
        gap = 5

        draw.rectangle([center_x-1, center_y-1, center_x+1, center_y+1], outline=color)

        draw.polygon([
            center_x, center_y - gap - 1,
            center_x - triangle_base//2, center_y - gap - triangle_height - 1,
            center_x + triangle_base//2, center_y - gap - triangle_height - 1
        ], fill=color, outline=color)

        draw.polygon([
            center_x, center_y + gap + 1,
            center_x - triangle_base//2, center_y + gap + triangle_height + 1,
            center_x + triangle_base//2, center_y + gap + triangle_height + 1
        ], fill=color, outline=color)

        draw.polygon([
            center_x - gap - 1, center_y,
            center_x - gap - triangle_height - 1, center_y - triangle_base//2,
            center_x - gap - triangle_height - 1, center_y + triangle_base//2
        ], fill=color, outline=color)

        draw.polygon([
            center_x + gap + 1, center_y,
            center_x + gap + triangle_height + 1, center_y - triangle_base//2,
            center_x + gap + triangle_height + 1, center_y + triangle_base//2
        ], fill=color, outline=color)

    # Thick border - overlap interior of big pixel
    def draw_special_crosshair_2(self, image, center, width, height, color, zoom):
        draw = ImageDraw.Draw(image)
        center_x, center_y = center

        # Calculate the edges of the critical pixel
        left_edge = center_x - zoom // 2
        right_edge = left_edge + zoom - 1
        top_edge = center_y - zoom // 2
        bottom_edge = top_edge + zoom - 1

        # Draw a 5-pixel thick box around the critical pixel
        for i in range(5):
            draw.rectangle([left_edge-i, top_edge-i, right_edge+i, bottom_edge+i], outline=color)

        # Scale other elements
        triangle_base = max(13 * zoom // 16, 7)
        triangle_height = max(20 * zoom // 16, 10)
        gap = max(5 * zoom // 16, 3)

        # Draw triangles
        draw.polygon([
            center_x, top_edge - gap - 5,
            center_x - triangle_base//2, top_edge - gap - triangle_height - 5,
            center_x + triangle_base//2, top_edge - gap - triangle_height - 5
        ], fill=color, outline=color)

        draw.polygon([
            center_x, bottom_edge + gap + 5,
            center_x - triangle_base//2, bottom_edge + gap + triangle_height + 5,
            center_x + triangle_base//2, bottom_edge + gap + triangle_height + 5
        ], fill=color, outline=color)

        draw.polygon([
            left_edge - gap - 5, center_y,
            left_edge - gap - triangle_height - 5, center_y - triangle_base//2,
            left_edge - gap - triangle_height - 5, center_y + triangle_base//2
        ], fill=color, outline=color)

        draw.polygon([
            right_edge + gap + 5, center_y,
            right_edge + gap + triangle_height + 5, center_y - triangle_base//2,
            right_edge + gap + triangle_height + 5, center_y + triangle_base//2
        ], fill=color, outline=color)

    # Thick border - outsize
    def draw_special_crosshair_3(self, image, center, width, height, color, zoom):
        draw = ImageDraw.Draw(image)
        center_x, center_y = center

        # Calculate the edges of the critical pixel
        left_edge = center_x - zoom // 2
        right_edge = left_edge + zoom - 1
        top_edge = center_y - zoom // 2
        bottom_edge = top_edge + zoom - 1

        # Draw a 5-pixel thick box around the critical pixel, entirely outside
        for i in range(5):
            draw.rectangle([left_edge-1-i, top_edge-1-i, right_edge+1+i, bottom_edge+1+i], outline=color)

        # Scale other elements
        triangle_base = max(13 * zoom // 16, 7)
        triangle_height = max(20 * zoom // 16, 10)
        gap = max(5 * zoom // 16, 3)

        # Draw triangles
        draw.polygon([
            center_x, top_edge - gap - 6,
            center_x - triangle_base//2, top_edge - gap - triangle_height - 6,
            center_x + triangle_base//2, top_edge - gap - triangle_height - 6
        ], fill=color, outline=color)

        draw.polygon([
            center_x, bottom_edge + gap + 6,
            center_x - triangle_base//2, bottom_edge + gap + triangle_height + 6,
            center_x + triangle_base//2, bottom_edge + gap + triangle_height + 6
        ], fill=color, outline=color)

        draw.polygon([
            left_edge - gap - 6, center_y,
            left_edge - gap - triangle_height - 6, center_y - triangle_base//2,
            left_edge - gap - triangle_height - 6, center_y + triangle_base//2
        ], fill=color, outline=color)

        draw.polygon([
            right_edge + gap + 6, center_y,
            right_edge + gap + triangle_height + 6, center_y - triangle_base//2,
            right_edge + gap + triangle_height + 6, center_y + triangle_base//2
        ], fill=color, outline=color)



    def update_texture(self):
        if self.texture:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            if canvas_width > 1 and canvas_height > 1:
                self.texture_image = self.create_tiled_texture(canvas_width, canvas_height)
                self.canvas.delete("texture")
                self.canvas.create_image(0, 0, anchor=tk.NW, image=self.texture_image, tags="texture")
            else:
                self.parent.after(100, self.update_texture)  # Try again after a short delay
        else:
            self.canvas.delete("texture")
            self.canvas.configure(bg='white')

    def create_tiled_texture(self, width, height):
        tile_size = 20  # or whatever size you want for the base texture tile
        base_texture = self.create_base_texture(tile_size)
        
        # Create a larger image by tiling the base texture
        tiled_texture = Image.new('RGB', (width, height))
        for y in range(0, height, tile_size):
            for x in range(0, width, tile_size):
                tiled_texture.paste(base_texture, (x, y))
        
        return ImageTk.PhotoImage(tiled_texture)

    def create_base_texture(self, tile_size):
        texture = Image.new('RGB', (tile_size, tile_size), color='white')
        draw = ImageDraw.Draw(texture)

        if self.texture == "check_1":
            for i in range(0, tile_size, tile_size // 2):
                for j in range(0, tile_size, tile_size // 2):
                    if (i + j) // (tile_size // 2) % 2 == 0:
                        draw.rectangle([i, j, i + tile_size // 2, j + tile_size // 2], fill='lightgray')
        elif self.texture == "check_2":
            for i in range(0, tile_size, tile_size // 2):
                for j in range(0, tile_size, tile_size // 2):
                    if (i // (tile_size // 2) + j // (tile_size // 2)) % 2 == 0:
                        draw.rectangle([i, j, i + tile_size // 2, j + tile_size // 2], fill=(69, 69, 69))
        
        return texture



    
    # These functions are for accepting outside inpute
    ######################

    def set_texture(self, texture: str):
        self.texture = texture
        self.update_texture()

    def set_show_texture_on_stop(self, show_texture_on_stop: bool):
        self.show_texture_on_stop = show_texture_on_stop

    def set_multiplier(self, multiplier: int):
        self.multiplier = multiplier

    def set_target(self, target: Callable[[], Tuple[int, int]]):
        self.target = target
        
    def set_crosshair(self, crosshair: str):
        self.crosshair = crosshair

    def set_crosshair_color(self, color: str):
        self.color = color

    def set_crosshair_opacity(self, opacity: float):
        self.opacity = opacity

    def set_invert_crosshair(self, invert: bool):
        self.invert_crosshair = invert

    def set_maintain_aspect(self, maintain_aspect: bool):
        self.maintain_aspect = maintain_aspect

    def set_show_texture(self, show_texture: bool):
        self.show_texture = show_texture
        if show_texture and not self.viewer_thread:
            self.canvas.itemconfigure("texture", state="normal")
        else:
            self.canvas.itemconfigure("texture", state="hidden")

    def invert_image(self, image, crosshair_type, color):
        # Apply inversion mask
        inverted = ImageChops.invert(image)
        mask = Image.new('L', image.size, 0)
        draw_mask = ImageDraw.Draw(mask)

        center = (image.width // 2, image.height // 2)
        if crosshair_type == "boxhair":
            draw_mask.rectangle([center[0]-1, center[1]-1, center[0]+1, center[1]+1], outline=255, width=1)
            draw_mask.line([center[0], 0, center[0], image.height], fill=255)
            draw_mask.line([0, center[1], image.width, center[1]], fill=255)
        # ... (other crosshair types)
        image = Image.composite(inverted, image, mask)
        return image






################
#              #
#   Test App   #   Pointed only at the mouse. 
#              #
################

class PixelViewerTestApp:
    def __init__(self, master):
        self.master = master
        self.master.title("PixelViewer Test App")
        self.master.geometry("310x500")

        self.style = ttk.Style()
        self.style.theme_use('xpnative')
        
        self.master.grid_rowconfigure(1, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

        self.info_frame = ttk.LabelFrame(self.master, text="Info:")
        self.info_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(2, 5))

        self.info_label = ttk.Label(self.info_frame, text=f"PixelViewer Test Application - PixelViewer v{VERSION}\nTarget: Mouse. | A host app can pass a dynamic target.\nAll controls exposed here.")
        self.info_label.pack(fill=tk.BOTH, expand=True)

        self.viewer_labelframe = ttk.LabelFrame(self.master, text="PixelViewer")
        self.viewer_labelframe.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        self.viewer_labelframe.grid_rowconfigure(0, weight=1)
        self.viewer_labelframe.grid_columnconfigure(0, weight=1)

        self.viewer_frame = ttk.Frame(self.viewer_labelframe, borderwidth=2, relief="sunken")
        self.viewer_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=(0, 5))
        self.viewer_frame.grid_rowconfigure(0, weight=1)
        self.viewer_frame.grid_columnconfigure(0, weight=1)

        # Initialize debug_mode_var before using it
        self.debug_mode_var = tk.BooleanVar(value=False)
        
        self.pixel_viewer = PixelViewer(self.viewer_frame, frame_rate=60, texture="check_1", show_texture_on_stop=False, debug_mode=self.debug_mode_var.get())
        self.pixel_viewer.canvas.grid(row=0, column=0, sticky="nsew")
        
        self.pixel_viewer.update_texture()  # Ensure texture is updated after grid placement

        self.controls_frame = ttk.LabelFrame(self.master, text="Controls:")
        self.controls_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 5))

        self.setup_controls()

    def setup_controls(self):
        self.multiplier_var = tk.StringVar(value="16")
        self.crosshair_var = tk.StringVar(value="None")
        self.color_var = tk.StringVar(value="#ff0000")
        self.opacity_var = tk.DoubleVar(value=1.0)
        self.invert_crosshair_var = tk.BooleanVar(value=False)
        self.maintain_aspect_var = tk.BooleanVar(value=True)
        self.texture_var = tk.StringVar(value="check_1")
        self.show_texture_on_stop_var = tk.BooleanVar(value=False)

        controls = [
            ("Texture:", self.texture_var, ["None", "check_1", "check_2"]),
            ("Multiplier:", self.multiplier_var, None),
            ("Crosshair:", self.crosshair_var, ["None", "pixel", "cross", "plus", "box", "thiccbox", "boxhair", "boxhair_2", "special", "special_2", "special_3"]),
            ("Color:", self.color_var, None),
            ("Opacity:", self.opacity_var, (0.0, 1.0))
        ]

        for i, (label, var, options) in enumerate(controls):
            ttk.Label(self.controls_frame, text=label).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            if options is None:
                ttk.Entry(self.controls_frame, textvariable=var).grid(row=i, column=1, sticky="we", padx=5, pady=2)
            elif isinstance(options, list):
                ttk.Combobox(self.controls_frame, textvariable=var, values=options).grid(row=i, column=1, sticky="we", padx=5, pady=2)
            elif isinstance(options, tuple):
                ttk.Scale(self.controls_frame, from_=options[0], to=options[1], variable=var, orient=tk.HORIZONTAL).grid(row=i, column=1, sticky="we", padx=5, pady=2)

        # Checkboxes and buttons side by side, each arranged vertically
        checkbox_frame = ttk.Frame(self.controls_frame)
        checkbox_frame.grid(row=len(controls), column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        checkboxes = [
            ("Invert Crosshair", self.invert_crosshair_var),
            ("Show texture on stop", self.show_texture_on_stop_var),
            ("Debug Mode", self.debug_mode_var, self.toggle_debug_mode)
        ]
        
        for i, checkbox_info in enumerate(checkboxes):
            text, var = checkbox_info[:2]
            command = checkbox_info[2] if len(checkbox_info) > 2 else None
            ttk.Checkbutton(checkbox_frame, text=text, variable=var, command=command).grid(row=i, column=0, sticky="w", padx=(0,5), pady=2)

        
        button_frame = ttk.Frame(checkbox_frame)
        button_frame.grid(row=0, column=1, rowspan=3, sticky="ns", padx=(5,0))
        
        self.apply_button = ttk.Button(button_frame, text="Apply Settings", width=15, command=self.apply_settings)
        self.apply_button.grid(row=0, column=0, pady=(0,5), sticky="ew")
        self.viewer_button = ttk.Button(button_frame, text="Start Viewer", width=15, command=self.toggle_viewer)
        self.viewer_button.grid(row=1, column=0, sticky="ew")

        self.controls_frame.grid_columnconfigure(1, weight=1)
        checkbox_frame.grid_columnconfigure(1, weight=1)

    def toggle_debug_mode(self):
        self.pixel_viewer.debug_mode = self.debug_mode_var.get()
        print(f"Debug mode {'enabled' if self.pixel_viewer.debug_mode else 'disabled'}")

    def apply_settings(self):
        self.apply_button.config(text="[WAIT]", width=15)
        self.master.update_idletasks()  # Force update of button text
        
        self.pixel_viewer.set_multiplier(int(self.multiplier_var.get()))
        self.pixel_viewer.set_crosshair(self.crosshair_var.get())
        self.pixel_viewer.texture = self.texture_var.get()
        self.pixel_viewer.set_show_texture_on_stop(self.show_texture_on_stop_var.get())
        self.pixel_viewer.set_crosshair_color(self.color_var.get())
        self.pixel_viewer.set_crosshair_opacity(self.opacity_var.get())
        self.pixel_viewer.set_invert_crosshair(self.invert_crosshair_var.get())
        self.pixel_viewer.debug_mode = self.debug_mode_var.get()

        self.pixel_viewer.update_texture()

        if self.pixel_viewer.viewer_thread and self.pixel_viewer.viewer_thread.is_alive():
            self.pixel_viewer.stop_viewer()
            self.pixel_viewer.start_viewer()

        self.apply_button.config(text="Apply Settings")

    def toggle_viewer(self):
        self.viewer_button.config(text="Viewer [WAIT]")
        self.master.update_idletasks()
        
        if not self.pixel_viewer.viewer_thread or not self.pixel_viewer.viewer_thread.is_alive():
            self.pixel_viewer.start_viewer()
            self.master.after(100, self.check_viewer_started)
        else:
            self.pixel_viewer.stop_viewer()
            self.viewer_button.config(text="Start Viewer")
            self.pixel_viewer.update_texture()

    def check_viewer_started(self):
        if self.pixel_viewer.viewer_thread and self.pixel_viewer.viewer_thread.is_alive():
            self.viewer_button.config(text="Viewer [On]", width=15)
        else:
            self.master.after(100, self.check_viewer_started)
            

if __name__ == "__main__":
    root = tk.Tk()
    app = PixelViewerTestApp(root)
    root.mainloop()