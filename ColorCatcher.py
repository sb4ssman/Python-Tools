# -*- coding: utf-8 -*-
"""
Created on Fri Jun 16 07:06:23 2024

@author: Thomas
"""



# ColorCatcher
# This standalone tool can be used to capture the color from underneath your mouse pointer

# Screenshot: will capture a screenshot and bring the tool to the front; useful if you want to sample something that is uncooperative with your clicks


import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import ImageGrab, ImageTk, Image, ImageDraw
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

        self.root = root
        self.root.title("ColorCatcher")
        self.root.geometry("420x420")
        self.root.attributes("-topmost", True)

        self.setup_gui()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)



    def setup_gui(self):
        main_frame = ttk.Frame(self.root, padding=5)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # # Instructions text box
        instructions_text = "Instructions:\n" \
                            "1. Click 'Start' to begin catching colors.\n" \
                            "2. Hover over the desired color; press 'T'.\n" \
                            "3. Press 'Escape' to stop catching colors.\n" \
                            "4. Click 'Save' to save the caught colors."
        # instructions_label = tk.Text(main_frame, height=5, wrap=tk.WORD, bg="lightgray")
        # instructions_label.insert(tk.END, instructions_text)
        # instructions_label.config(state=tk.DISABLED)
        # instructions_label.pack(fill=tk.X, padx=5, pady=5)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.start_stop_button = ttk.Button(button_frame, text="Start", command=self.toggle_capture)
        self.start_stop_button.pack(side=tk.LEFT, padx=5)
        
        # self.start_stop_button.bind("<space>", lambda event: None)  # Prevent spacebar from triggering the button, so we can use it for color catching!
        # self.root.bind("<space>", lambda event: self.catch_color())  # Bind space to catch_color


        self.save_button = ttk.Button(button_frame, text="Save", command=self.save_colors)
        self.save_button.pack(side=tk.LEFT, padx=5)


        # self.use_screenshot_var = tk.BooleanVar(value=False)
        # self.use_screenshot_checkbox = ttk.Checkbutton(button_frame, text="Screenshot", variable=self.use_screenshot_var)
        # self.use_screenshot_checkbox.pack(side=tk.RIGHT, padx=5) # We pack this one first to make it farthest right
        # createToolTip(self.use_screenshot_checkbox, "Snap and overlay a screenshot\nto collect uncooperative samples.\nEsc or spacebar will STOP.")





        zoom_dropdown = ttk.Combobox(button_frame, textvariable=self.zoom_multiplier, values=list(range(1, 65)), width=2) # I could let it go higher, but 64 is plenty
        zoom_dropdown.pack(side=tk.RIGHT, padx=5)
        zoom_dropdown.current(15) # default value = 16
        ttk.Label(button_frame, text="1px =").pack(side=tk.RIGHT, padx=5)


        self.instructions_hover = ttk.Label(button_frame, text="Hover for\ninstructions")
        self.instructions_hover.pack(side=tk.RIGHT)
        createToolTip(self.instructions_hover, instructions_text)

        self.paned_window = ttk.Panedwindow(main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(self.paned_window, relief=tk.SUNKEN)
        left_frame.pack_propagate(False)
        self.paned_window.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Caught Colors:").pack(anchor=tk.CENTER, padx=5, pady=5)

        self.color_listbox = tk.Listbox(left_frame, height=20, width=30)
        self.color_listbox.pack(fill=tk.BOTH, expand=True)
        self.color_listbox.bind('<<ListboxSelect>>', self.on_color_select)

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

        # self.root.bind('<Escape>', self.stop_capture)
        # self.root.bind('<space>', self.stop_capture)

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
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'w') as f:
                f.write("\n".join(self.colors))
            messagebox.showinfo("Save Successful", "Colors catched successfully!")


    # Select a caught color from list, see it in the canvas
    def on_color_select(self, event):
        try:
            selection = event.widget.curselection()
            if selection:
                index = selection[0]
                color_hex = event.widget.get(index)
                self.color_canvas.create_rectangle(0, 0, self.color_canvas.winfo_width(), self.color_canvas.winfo_height(), fill=color_hex)
        except Exception as e:
            print(f"Error selecting color: {e}")


    # could you even catch them all?
    def catch_color(self, event=None):
        try:
            # Get the color from the color_canvas
            color_hex = self.current_color
            if color_hex:
                self.colors.append(color_hex)
                self.color_listbox.insert(tk.END, color_hex)
                self.color_canvas.create_rectangle(0, 0, self.color_canvas.winfo_width(), self.color_canvas.winfo_height(), fill=color_hex)
        except Exception as e:
            print(f"Error catching color: {e}")




    def toggle_capture(self):
        if self.capturing:
            self.stop_capture()
        else:
            self.capturing = True
            self.stop_threads = False
            self.start_stop_button.config(text="Stop")
            self.root.config(cursor="cross")
            # self.root.bind("<Button-1>", self.catch_color)
            self.root.bind("<c>", lambda event: self.catch_color())  # Bind C to catch_color
            self.root.bind("<Escape>", self.stop_capture)

            self.root.grab_set()  # Ensure the application captures all mouse events

            self.update_zoomed_thread = threading.Thread(target=self.update_zoomed_view, name="Thread-1 (update_zoomed_view)")
            self.update_zoomed_thread.daemon = True
            self.update_zoomed_thread.start()

            self.update_color_display_thread = threading.Thread(target=self.update_color_display, name="Thread-2 (update_color_display)")
            self.update_color_display_thread.daemon = True
            self.update_color_display_thread.start()

            print("Started update_zoomed_view and update_color_display threads")






    # The threads tended to come unraveled, so this method gets a lot of prints and trys
    def stop_capture(self, event=None):
        if event and event.keysym != "Escape": # Look for escape specifically
            return

        print("Stopping capture mode...")
        self.stop_threads = True
        self.capturing = False

        # Edit the buttonm in a try wrapper in case the window is already closed; want to do this beacuse sometimes it takes a moment
        try:
            self.start_stop_button.config(text="STOPPING")
        except:
            pass


        # self.start_stop_button.config(text="Start")
        self.root.config(cursor="")
        self.root.unbind("<Button-1>")
        self.root.unbind("<space>")
        self.root.unbind("<Escape>")
        self.root.grab_release()  # Release the mouse capture

        self.color_canvas.delete("all")
        self.color_canvas.create_image(0, 0, anchor=tk.NW, image=self.transparency_tk, tags="transparency")


        if self.overlay:
            self.overlay.destroy()
            self.overlay = None

        # print("Active threads before joining:", threading.enumerate())

        try:
            if self.update_zoomed_thread and self.update_zoomed_thread.is_alive():
                # print("Joining update_zoomed_thread")
                self.update_zoomed_thread.join(timeout=1)
                print("update_zoomed_thread joined")
            else:
                print("update_zoomed_thread not alive or does not exist")
        except AttributeError as e:
            print(f"update_zoomed_thread error: {e}")

        try:
            if self.update_color_display_thread and self.update_color_display_thread.is_alive():
                # print("Joining update_color_display_thread")
                self.update_color_display_thread.join(timeout=1)
                print("update_color_display_thread joined")
            else:
                print("update_color_display_thread not alive or does not exist")
        except AttributeError as e:
            print(f"update_color_display_thread error: {e}")       

        #print("Active threads after joining:", threading.enumerate())



        # Additional thread exit confirmation
        for thread in threading.enumerate():
            if thread.name.startswith("Thread-") and thread.is_alive():
                print(f"Thread {thread.name} is still alive")
                # Force thread to stop if it hasn't exited properly
                thread.join(timeout=1)
                print(f"Attempting to force join {thread.name}")
                if thread.is_alive():
                    print(f"Thread {thread.name} is still alive after force join attempt")
            else:
                print(f"Thread {thread.name} has exited")

        # And fix the button
        self.start_stop_button.config(text="Start")


















    def update_zoomed_view(self):
        print("Starting update_zoomed_view thread")
        while not self.stop_threads:
            # print(f"Running update_zoomed_view loop, stop_threads={self.stop_threads}")
            try:
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
            except Exception as e:
                print(f"Error in update_zoomed_view: {e}")
            time.sleep(0.1)
        print("Exiting update_zoomed_view thread completely")







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
                color_hex = f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
                self.current_color = color_hex
                self.color_canvas.delete("transparency")
                self.color_canvas.create_rectangle(0, 0, self.color_canvas.winfo_width(), self.color_canvas.winfo_height(), fill=color_hex)
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
