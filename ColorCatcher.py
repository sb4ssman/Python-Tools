# -*- coding: utf-8 -*-
"""
Created on Fri Jun 16 07:06:23 2024

@author: Thomas
"""


# ColorCatcher
# This standalone tool can be used to capture the color from underneath your mouse pointer

# NOTE: most of the layout and usability of the GUI were inspired by a tutorial I cannot find. I would love to give someone the credit they deserve. 
#       Detials that I added include selecting captured colors to view again, sending a specific color to the viewer, crosshairs, and letting the viewers expand.

# Screenshot: will capture a screenshot and bring the tool to the front; useful if you want to sample something that is uncooperative with your clicks


VERSION = 1.0 # I am pleased with it. 


# Could add: better export options


import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import ImageGrab, ImageTk, Image, ImageDraw
from datetime import datetime
import colorsys
import pyautogui
import threading
import time



# I wanted one tooltip. 

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self):
        "Display text in tooltip window" # "Snap and overlay a screenshot\nto collect uncooperative samples.\nEsc or spacebar will STOP."
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        tw.attributes("-topmost", True)  # Ensure tooltip is on top
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                      background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def createToolTip(widget, text):
    toolTip = ToolTip(widget, text)
    def enter(event):
        toolTip.showtip()
    def leave(event):
        toolTip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)


# Example Usage:
# screenshot_checkbox = tk.Checkbutton(root, text="Use Screenshot")
# screenshot_checkbox.pack(side=tk.RIGHT, padx=5)
# createToolTip(screenshot_checkbox, "Capture the screen when clicking colors")






####################
#
# COLOR CATCHER
#
##################

class ColorCatcher:
    def __init__(self, root):
        self.capturing = False
        self.colors = []
        self.zoom_multiplier = tk.IntVar(value=4)
        self.stop_threads = False
        self.overlay = None
        self.score = 0

        self.root = root
        self.root.title("ColorCatcher")
        self.root.geometry("420x420")
        self.root.attributes("-topmost", True)

        ttk.Style().theme_use('xpnative')

        self.setup_gui()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)



    def setup_gui(self):
        main_frame = ttk.Frame(self.root, padding=5)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # # Instructions text 
        instructions_text = "Instructions:\n" \
                            "1. Click 'Start' to begin catching colors.\n" \
                            "2. Hover over the desired color; press 'C'.\n" \
                            "3. Press 'Escape' or <spacebar> to stop.\n" \
                            "4. Click 'Save' to save the caught colors.\n" \
                            "Note: clicking can disrupt catching. "
        # instructions_label = tk.Text(main_frame, height=5, wrap=tk.WORD, bg="lightgray")
        # instructions_label.insert(tk.END, instructions_text)
        # instructions_label.config(state=tk.DISABLED)
        # instructions_label.pack(fill=tk.X, padx=5, pady=5)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        button_style = ttk.Style()
        button_style.configure("Compact.TButton", padding=(5, 2), font=("Arial", 10))


        self.start_stop_button = ttk.Button(button_frame, text="Start", command=self.toggle_capture, style="Compact.TButton", width=6)
        self.start_stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # self.start_stop_button.bind("<space>", lambda event: None)  # Prevent spacebar from triggering the button, so we can use it for color catching!
        # self.root.bind("<space>", lambda event: self.catch_color())  # Bind space to catch_color


        self.save_button = ttk.Button(button_frame, text="Save", command=self.save_colors, style="Compact.TButton", width=6)
        self.save_button.pack(side=tk.LEFT, padx=5)

        # I rather like how this turned out
        self.instructions_hover = ttk.Label(button_frame, text="Hover for\ninstructions")
        self.instructions_hover.pack(side=tk.LEFT, padx=5)
        createToolTip(self.instructions_hover, instructions_text)

        # Multiplier
        zoom_dropdown = ttk.Combobox(button_frame, textvariable=self.zoom_multiplier, values=[1, 2, 3, 4, 8, 16, 32, 64, 128], width=3) # Any arbitrary integer should work
        zoom_dropdown.pack(side=tk.RIGHT, padx=0)
        zoom_dropdown.current(5) # default value = 16
        ttk.Label(button_frame, text="1px =").pack(side=tk.RIGHT, padx=0)
        createToolTip(zoom_dropdown, "Select pixel multiplier.\n" \
                                            "You can input integer values, and\n" \
                                            "you can resize the window to view\n" \
                                            "more of the area around your mouse." \
                                            )

        # Screenshot checkbox - pack this one after the dropdown because RIGHT-to-left when packed RIGHT
        self.use_screenshot_var = tk.BooleanVar(value=False)
        self.use_screenshot_checkbox = ttk.Checkbutton(button_frame, text="Screenshot", variable=self.use_screenshot_var)
        self.use_screenshot_checkbox.pack(side=tk.RIGHT, padx=(0, 10)) 
        createToolTip(self.use_screenshot_checkbox, "Snap and overlay a screenshot\n" \
                                                    "to collect uncooperative samples.\n" \
                                                    "Esc or spacebar will STOP.\n\n" \
                                                    "To sample something that only\n" \
                                                    "occurs during a click, you might\n" \
                                                    "try holding the click and hitting\n" \
                                                    "'PrtScr' on your keyboard. Paste\n" \
                                                    "the result somewhere to sample."
                                                    )


        self.paned_window = ttk.Panedwindow(main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(self.paned_window) # , relief=tk.SUNKEN
        left_frame.pack_propagate(False)
        self.paned_window.add(left_frame, weight=1)

        # The Catcher Label
        self.catcher_str = tk.StringVar()
        self.catcher_str.set(f"Caught Colors: {self.score}")
        self.catcher_label = ttk.Label(left_frame, textvariable=self.catcher_str) # , relief="sunken"
        self.catcher_label.pack(anchor=tk.CENTER, padx=5, pady=5)


        self.color_listbox = tk.Listbox(left_frame, height=18, width=30)
        self.color_listbox.pack(fill=tk.BOTH, expand=True)
        self.color_listbox.bind('<<ListboxSelect>>', self.on_color_select)

        # Color input 
        # Add custom styles for the input frame and label to blend them into the surrounding frame
        style = ttk.Style()
        style.configure("Custom.TFrame", background="#f0f0f0", relief="flat")
        style.configure("Custom.TLabel", background="#f0f0f0", relief="flat")

        input_frame = ttk.Frame(left_frame, style="Custom.TFrame", relief=tk.FLAT, borderwidth=0)  # , relief="flat", borderwidth=0
        input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        self.color_entry = tk.Entry(input_frame, width=10)
        self.color_entry.insert(0, "#")  # Set default text
        self.color_entry.pack(side=tk.LEFT, padx=(0, 5))

        # We can make sure that pound sign stays just where it is
        def keep_hash(event):
            if not self.color_entry.get().startswith("#"):
                self.color_entry.insert(0, "#")
        self.color_entry.bind("<FocusOut>", keep_hash)
        self.color_entry.bind("<KeyRelease>", keep_hash)

        self.color_entry.bind("<Return>", lambda event: self.send_color_to_preview())  # Bind Enter key

        self.send_button = ttk.Button(input_frame, text=">", command=self.send_color_to_preview, style="Compact.TButton", width=2)
        self.send_button.pack(side=tk.LEFT)
        createToolTip(self.send_button, "Send a color to the field.")

        self.current_color_label = ttk.Label(input_frame, text="(None):", relief="flat", borderwidth=0)
        self.current_color_label.pack(side=tk.RIGHT, padx=(5, 10))







        # Right frame
        self.right_frame = ttk.Frame(self.paned_window, relief=tk.SUNKEN)
        self.right_frame.pack_propagate(False)
        self.paned_window.add(self.right_frame, weight=1)

        self.right_paned_window = ttk.Panedwindow(self.right_frame, orient=tk.VERTICAL)
        self.right_paned_window.pack(side=tk.TOP, fill=tk.BOTH, expand=True)


        # Zoom view
        zoomed_frame = ttk.Frame(self.right_paned_window, relief=tk.SUNKEN, borderwidth=0)
        zoomed_frame.pack_propagate(False)
        self.right_paned_window.add(zoomed_frame, weight=1)

        self.zoomed_canvas = tk.Canvas(zoomed_frame, bg='grey', highlightthickness=0)
        self.zoomed_canvas.pack(fill=tk.BOTH, expand=True)

        # Ensure the zoomed view scales correctly
        self.zoomed_canvas.bind("<Configure>", self.update_zoomed_view)


        # Color view
        color_frame = ttk.Frame(self.right_paned_window, relief=tk.SUNKEN, borderwidth=0)
        color_frame.pack_propagate(False)
        self.right_paned_window.add(color_frame, weight=1)

        self.color_canvas = tk.Canvas(color_frame, bg='white', width=200, height=200, highlightthickness=0)
        self.color_canvas.pack(fill=tk.BOTH, expand=True)

        self.color_canvas.bind("<Configure>", self.on_color_canvas_resize)

        # Grid setup
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.root.update_idletasks()

        
        self.root.after(100, self.center_panes)

        print("GUI setup complete.")




    def center_panes(self):
        self.root.update_idletasks()
        self.paned_window.sashpos(0, self.root.winfo_width() // 2)
        self.right_paned_window.sashpos(0, self.right_frame.winfo_height() // 2)

    def on_closing(self):
        self.stop_capture()
        self.root.destroy()

    def save_colors(self):
        self.stop_capture()  # Stop capturing before saving
        print("Saving colors...")
        now = datetime.now().strftime("%Y-%m-%d")
        suggested_file_name = f"{now}--{self.score}-colorscaught.txt"
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=suggested_file_name, filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'w') as f:
                f.write(f"ColorCatcher\nDate: {now}\nScore: {self.score}\n\n")
                for color in self.colors:
                    f.write(f"{color}\n")
            messagebox.showinfo("Save Successful", f"{self.score} color(s) caught successfully!")
            # could open the file or folder after save?

    # For previewing a specific code
    def send_color_to_preview(self):
        try:
            color_hex = self.color_entry.get().strip()
            if not color_hex.startswith("#"):
                color_hex = f"#{color_hex}"
            # Validate the hex color format
            if len(color_hex) == 7 and all(c in '0123456789ABCDEFabcdef' for c in color_hex[1:]):
                self.color_canvas.create_rectangle(0, 0, self.color_canvas.winfo_width(), self.color_canvas.winfo_height(), fill=color_hex)
                self.current_color_label.config(text=f"{color_hex}:")
            else:
                raise ValueError("Invalid Color")
        except Exception as e:
            self.current_color_label.config(text=f"Invalid Color!")


    # Select a caught color from list, see it in the canvas
    def on_color_select(self, event):
        try:
            selection = event.widget.curselection()
            if selection:
                index = selection[0]
                color_entry = event.widget.get(index)
                hex = color_entry.split(",")[0]
                self.color_canvas.create_rectangle(0, 0, self.color_canvas.winfo_width(), self.color_canvas.winfo_height(), fill=hex)
                self.current_color_label.config(text=f"{hex}:")
        except Exception as e:
            print(f"Error selecting color: {e}")


    # could you even catch them all?
    def catch_color(self, event=None):
        try:
            # Get the color from the color_canvas
            rgb = self.current_color
            if rgb:
                hex = f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
                hsv = colorsys.rgb_to_hsv(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)
                hsv = tuple(round(i * 255) for i in hsv)
                color_entry = f"{hex}, RGB: {rgb}, HSV: {hsv}"
                self.colors.append(color_entry)
                self.color_listbox.insert(tk.END, color_entry)
                self.color_canvas.create_rectangle(0, 0, self.color_canvas.winfo_width(), self.color_canvas.winfo_height(), fill=hex)
                self.score += 1
                self.catcher_str.set(f"Press C to catch! ({self.score})")

        except Exception as e:
            print(f"Error catching color: {e}")




    def toggle_capture(self):
        if self.capturing:
            self.stop_capture()
        else:
            self.catcher_str.set(f"Press C to catch! ({self.score})")
            self.capturing = True
            self.stop_threads = False
            self.start_stop_button.config(text="Stop")
            self.current_color_label.config(text="")
            self.root.bind("<c>", lambda event: self.catch_color())
            self.root.bind("<Escape>", self.stop_capture)
            self.root.bind("<space>", self.stop_capture)

            self.root.grab_set()

            if self.use_screenshot_var.get():
                self.fullscreen_screenshot()

            # Start threads for viewers
            self.update_zoomed_thread = threading.Thread(target=self.run_zoomed_view_update)
            self.update_zoomed_thread.daemon = True
            self.update_zoomed_thread.start()

            self.update_color_display_thread = threading.Thread(target=self.update_color_display)
            self.update_color_display_thread.daemon = True
            self.update_color_display_thread.start()

            print("Started update_zoomed_view and update_color_display threads")

    def run_zoomed_view_update(self):
        while not self.stop_threads:
            self.update_zoomed_view()
            time.sleep(0.1)
        print("Exiting update_zoomed_view thread completely")





    # The threads tended to come unraveled, so this method gets a lot of prints and trys
    def stop_capture(self, event=None):
        if event and event.keysym != "Escape":
            return

        print("Stopping capture mode...")
        self.stop_threads = True
        self.capturing = False
        self.catcher_str.set(f"Caught colors: ({self.score})")
        try:
            self.start_stop_button.config(text="WAIT")
            self.root.update_idletasks()
        except:
            pass

        self.root.config(cursor="")
        self.root.unbind("<Button-1>")
        self.root.unbind("<space>")
        self.root.unbind("<Escape>")
        self.root.grab_release()

        self.color_canvas.delete("all")
        self.color_canvas.create_image(0, 0, anchor=tk.NW, image=self.transparency_tk, tags="transparency")

        if self.overlay:
            self.overlay.destroy()
            self.overlay = None

        try:
            if hasattr(self, 'update_zoomed_thread') and self.update_zoomed_thread.is_alive():
                self.update_zoomed_thread.join(timeout=1)
                print("update_zoomed_thread joined")
            else:
                print("update_zoomed_thread not alive or does not exist")
        except AttributeError as e:
            print(f"update_zoomed_thread error: {e}")

        try:
            if hasattr(self, 'update_color_display_thread') and self.update_color_display_thread.is_alive():
                self.update_color_display_thread.join(timeout=1)
                print("update_color_display_thread joined")
            else:
                print("update_color_display_thread not alive or does not exist")
        except AttributeError as e:
            print(f"update_color_display_thread error: {e}")

        for thread in threading.enumerate():
            if thread.name.startswith("Thread-") and thread.is_alive():
                print(f"Thread {thread.name} is still alive")
                thread.join(timeout=1)
                print(f"Attempting to force join {thread.name}")
                if thread.is_alive():
                    print(f"Thread {thread.name} is still alive after force join attempt")
            else:
                print(f"Thread {thread.name} has exited")

        self.start_stop_button.config(text="Start")










     
    # Update zoomed view            # EXCELLENT... up to level 32; 64 and 128 break the viewer.
    def update_zoomed_view(self, event=None):
        if not self.capturing:
            return

        try:
            x, y = pyautogui.position()
            zoom = max(1, int(self.zoom_multiplier.get()))
            canvas_width = self.zoomed_canvas.winfo_width()
            canvas_height = self.zoomed_canvas.winfo_height()

            # Ensure odd number of pixels in both directions
            region_width = (canvas_width // zoom) | 1
            region_height = (canvas_height // zoom) | 1

            # Adjust the region to ensure the critical pixel is centered
            region_x = x - region_width // 2
            region_y = y - region_height // 2

            im = pyautogui.screenshot(region=(region_x, region_y, region_width, region_height))
            
            # Resize maintaining pixel aspect ratio
            zoomed_width = region_width * zoom
            zoomed_height = region_height * zoom
            zoomed_im = im.resize((zoomed_width, zoomed_height), Image.NEAREST)
            self.zoomed_im_tk = ImageTk.PhotoImage(zoomed_im)

            # Clear the canvas
            self.zoomed_canvas.delete("all")

            # Calculate offset to center the image
            offset_x = (canvas_width - zoomed_width) // 2
            offset_y = (canvas_height - zoomed_height) // 2

            # Draw the zoomed image
            self.zoomed_canvas.create_image(offset_x, offset_y, anchor=tk.NW, image=self.zoomed_im_tk)

            # Calculate the center of the zoomed image
            center_x = offset_x + zoomed_width // 2
            center_y = offset_y + zoomed_height // 2

            # Calculate the coordinates for the crosshair
            left = center_x - zoom // 2 - 1
            right = center_x + (zoom + 1) // 2
            top = center_y - zoom // 2 - 1
            bottom = center_y + (zoom + 1) // 2

            # Draw the crosshair
            self.zoomed_canvas.create_line(left, offset_y, left, offset_y + zoomed_height, fill="red")
            self.zoomed_canvas.create_line(right, offset_y, right, offset_y + zoomed_height, fill="red")
            self.zoomed_canvas.create_line(offset_x, top, offset_x + zoomed_width, top, fill="red")
            self.zoomed_canvas.create_line(offset_x, bottom, offset_x + zoomed_width, bottom, fill="red")

            self.zoomed_canvas.config(scrollregion=self.zoomed_canvas.bbox(tk.ALL))
        except Exception as e:
            print(f"Error in update_zoomed_view: {e}")



    def update_zoomed_view_thread(self):
        if self.capturing:
            self.update_zoomed_thread = threading.Thread(target=self.update_zoomed_view)
            self.update_zoomed_thread.start()



    def update_color_display(self):
        print("Starting update_color_display thread")
        while not self.stop_threads:
            try:
                x, y = pyautogui.position()
                rgb = pyautogui.screenshot().getpixel((x, y))
                hex = f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
                self.current_color = rgb
                self.color_canvas.delete("transparency")
                self.color_canvas.create_rectangle(0, 0, self.color_canvas.winfo_width(), self.color_canvas.winfo_height(), fill=hex)
                self.current_color_label.config(text=f"{hex}:")
            except Exception as e:
                print(f"Error in update_color_display: {e}")
            time.sleep(0.1)
        print("Exiting update_color_display thread completely")







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

    # def create_custom_cursor(self):
    #     cursor_size = 32
    #     cursor_image = tk.PhotoImage(width=cursor_size, height=cursor_size)
    #     cursor_image.put(("white",) * cursor_size, to=(0, 0, cursor_size, cursor_size))
    #     for i in range(cursor_size):
    #         cursor_image.put("black", to=(i, cursor_size // 2))
    #         cursor_image.put("black", to=(cursor_size // 2, i))
    #     for i in range(cursor_size // 2 - 1, cursor_size // 2 + 2):
    #         for j in range(cursor_size // 2 - 1, cursor_size // 2 + 2):
    #             cursor_image.put("white", to=(i, j))
    #     self.root.config(cursor="crosshair")


if __name__ == "__main__":
    root = tk.Tk()
    app = ColorCatcher(root)
    root.mainloop()
