# -*- coding: utf-8 -*-
"""
Created on Sun Jun 30 04:22:44 2024

@author: Thomas
"""


# An unreasonably fancy mouse tracker


# Windows uses a virtual desktop that may not translate directly to the pixels of your montior(s) 
# They all line up 1:1, but a monitor's origin pixel is not necessarily Window's (0,0)

# Use an offset calibrator, and set your values here:

win_offset_x = 7
win_offset_y = 0





import pyautogui
import tkinter as tk
from tkinter import ttk
import subprocess
import re

# Color schemes 
LIGHT_COLORS = {
    'clean': {
        'label_bg': "#e1e1e1",
        'hover_bg': "#c7e0f4",
        'click_bg': "#a9d1f5",
        'border_color': "#adadad",
        'hover_border': "#0078d7",
        'click_border': "#005499",
        'text_color': "#000000",
        'labelframe_bg': "#f0f0f0",
        'labelframe_fg': "#333333"
    },
    'retro': {
        'label_bg': "#f0f0f0",
        'hover_bg': "#f0f0f0",
        'click_bg': "#f0f0f0",
        'border_color': "#c0c0c0",
        'hover_border': "#a0a0a0",
        'click_border': "#a0a0a0",
        'text_color': "#000000",
        'labelframe_bg': "#e0e0e0",
        'labelframe_fg': "#000000"
    }
}

DARK_COLORS = {
    'clean': {
        'label_bg': "#2d2d2d",
        'hover_bg': "#3a3a3a",
        'click_bg': "#454545",
        'border_color': "#555555",
        'hover_border': "#777777",
        'click_border': "#999999",
        'text_color': "#ffffff",
        'labelframe_bg': "#383838",
        'labelframe_fg': "#ffffff"
    },
    'retro': {
        'label_bg': "#404040",
        'hover_bg': "#404040",
        'click_bg': "#404040",
        'border_color': "#808080",
        'hover_border': "#808080",
        'click_border': "#808080",
        'text_color': "#ffffff",
        'labelframe_bg': "#505050",
        'labelframe_fg': "#ffffff"
    }
}






#########################
#                       #
#   FANCYBUTTON CLASS   #
#                       #
#########################

class FancyButton:
    def __init__(self, parent, create_surface, theme_var, dark_mode_var, command):
        self.parent = parent
        self.create_surface = create_surface
        self.theme_var = theme_var
        self.dark_mode_var = dark_mode_var
        self.command = command
        self.style = ttk.Style()
        self.widget_info = {}
        self.custom_attributes = {}

        self.outer_frame = tk.Frame(self.parent, bd=0, highlightthickness=0)
        self.inner_frame = tk.Frame(self.outer_frame, bd=0, highlightthickness=0)
        self.inner_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        self.surface = tk.Frame(self.inner_frame, bd=0, highlightthickness=0)
        self.surface.pack(fill=tk.BOTH, expand=False, padx=0, pady=0)

        self.widgets = self.create_surface(self.surface)

        self.is_hovered = False
        self.bind_events()
        self.update_style("")

    def create_widgets(self):
        def wrapper(*args, **kwargs):
            if 'font_size' in kwargs:
                font_size = kwargs.pop('font_size')
                widget = self.create_surface(self.surface)
                for w in widget:
                    if isinstance(w, (tk.Widget, ttk.Widget)):
                        self.custom_attributes[w] = {'font_size': font_size}
            else:
                widget = self.create_surface(self.surface)
            return widget
        return wrapper()

    def create_surface(self, surface):
        widgets = self.create_surface(surface)
        for widget in widgets:
            if isinstance(widget, tk.Widget):  # Only apply font directly to tk widgets
                font_size = self.get_font_size(widget)
                if hasattr(widget, 'configure'):
                    widget.configure(font=("TkDefaultFont", font_size))
        return widgets

    def bind_events(self):
        self.outer_frame.bind("<Enter>", self.on_enter)
        self.outer_frame.bind("<Leave>", self.on_leave)
        self.outer_frame.bind("<Button-1>", self.on_click)
        self.outer_frame.bind("<ButtonRelease-1>", self.on_release)
        self.inner_frame.bind("<Button-1>", self.on_click)
        self.inner_frame.bind("<ButtonRelease-1>", self.on_release)
        self.surface.bind("<Button-1>", self.on_click)
        self.surface.bind("<ButtonRelease-1>", self.on_release)
        self.bind_children(self.surface)

    def bind_children(self, widget):
        for child in widget.winfo_children():
            child.bind("<Enter>", lambda e, w=child: self.on_enter_child(e, w))
            child.bind("<Leave>", lambda e, w=child: self.on_leave_child(e, w))
            
            if not isinstance(child, (ttk.Scrollbar, ttk.Entry, ttk.Spinbox, ttk.Combobox, ttk.Scale, ttk.Checkbutton)):
                child.bind("<Button-1>", lambda e, w=child: self.on_click_child(e, w))
                child.bind("<ButtonRelease-1>", lambda e, w=child: self.on_release_child(e, w))
            
            if isinstance(child, (ttk.Radiobutton)):
                child.bind("<Button-1>", lambda e, w=child: self.on_interactive_widget_click(e, w), add="+")
                child.bind("<ButtonRelease-1>", lambda e, w=child: self.on_interactive_widget_release(e, w), add="+")
            
            if isinstance(child, ttk.Button):
                child.bind("<Button-1>", lambda e, w=child: self.on_inner_button_click(e, w))
                child.bind("<ButtonRelease-1>", lambda e, w=child: self.on_inner_button_release(e, w))
            
            if hasattr(child, 'winfo_children'):
                self.bind_children(child)

    def update_interactive_widget_state(self, event, widget):
        if isinstance(widget, ttk.Checkbutton):
            widget.toggle()
        elif isinstance(widget, ttk.Radiobutton):
            widget.invoke()
        self.update_style("Hover" if self.is_hovered else "")

    def on_enter(self, event):
        self.is_hovered = True
        self.update_style("Hover")

    def on_leave(self, event):
        self.is_hovered = False
        self.update_style("")

    def on_click(self, event):
        self.update_style("Click")
        self.collect_widget_info()

    def on_release(self, event):
        if self.is_mouse_within_bounds(event.x_root, event.y_root):
            self.command()
        self.update_style("Hover" if self.is_hovered else "")

    def on_enter_child(self, event, widget):
        if not self.is_hovered:
            self.is_hovered = True
            self.update_style("Hover")

    def on_leave_child(self, event, widget):
        if not self.is_mouse_within_bounds(event.x_root, event.y_root):
            self.is_hovered = False
            self.update_style("")

    def on_click_child(self, event, widget):
        self.update_style("Click")
        self.collect_widget_info()

    def on_release_child(self, event, widget):
        if self.is_mouse_within_bounds(event.x_root, event.y_root):
            if isinstance(widget, tk.Canvas):
                self.on_canvas_click(event, widget)
            self.command()
        self.update_style("Hover" if self.is_hovered else "")

    def on_inner_button_click(self, event, button):
        self.update_style("Click")
        self.collect_widget_info()
        if hasattr(button, 'invoke'):
            button.invoke()

    def on_inner_button_release(self, event, button):
        if self.is_mouse_within_bounds(event.x_root, event.y_root):
            self.command()
        self.update_style("Hover" if self.is_hovered else "")

    def on_interactive_widget_click(self, event, widget):
        self.update_style("Click")
        event.widget.event_generate("<<ThemeChanged>>")

    def on_interactive_widget_release(self, event, widget):
        if self.is_mouse_within_bounds(event.x_root, event.y_root):
            self.collect_widget_info()
        self.update_style("Hover" if self.is_hovered else "")
        event.widget.event_generate("<<ThemeChanged>>")
    
    def on_canvas_click(self, event, canvas):
        x, y = event.x, event.y
        self.widget_info[canvas.winfo_name()] = f"Clicked at ({x}, {y})"

    def update_style(self, state):
        theme = self.theme_var.get().lower()
        mode = "dark" if self.dark_mode_var.get() else "light"
        colors = DARK_COLORS[theme] if mode == "dark" else LIGHT_COLORS[theme]

        bg_color = colors['label_bg']
        fg_color = colors['text_color']

        if theme == "clean":
            if state == "Hover":
                self.outer_frame.config(bg=colors['hover_border'])
                self.inner_frame.config(bg=colors['hover_bg'])
                bg_color = colors['hover_bg']
            elif state == "Click":
                self.outer_frame.config(bg=colors['click_border'])
                self.inner_frame.config(bg=colors['click_bg'])
                bg_color = colors['click_bg']
            else:
                self.outer_frame.config(bg=colors['border_color'])
                self.inner_frame.config(bg=colors['label_bg'])
        elif theme == "retro":
            self.outer_frame.config(bg=colors['border_color'], relief="raised", bd=2)
            self.inner_frame.config(bg=colors['label_bg'])
            if state == "Click":
                self.outer_frame.config(relief="sunken")
            else:
                self.outer_frame.config(relief="raised")

        self.surface.config(bg=self.inner_frame.cget("bg"))
        self.style_descendants(self.surface, bg_color, fg_color, state)

        self.update_specific_widgets(self.surface, bg_color)

    def update_specific_widgets(self, widget, bg_color):
        for child in widget.winfo_children():
            if isinstance(child, ttk.Checkbutton):
                child.configure(style='TCheckbutton')
                self.style.configure('TCheckbutton', background=bg_color)
            elif isinstance(child, ttk.Radiobutton):
                child.configure(style='TRadiobutton')
                self.style.configure('TRadiobutton', background=bg_color)
            elif isinstance(child, ttk.Frame):
                child.configure(style='TFrame')
                self.style.configure('TFrame', background=bg_color)
            elif isinstance(child, tk.Frame):
                child.configure(bg=bg_color)
            
            if hasattr(child, 'winfo_children'):
                self.update_specific_widgets(child, bg_color)
        

    def style_descendants(self, widget, bg_color, fg_color, state):
        for child in widget.winfo_children():
            if isinstance(child, ttk.Widget):
                self.style_ttk_widget(child, bg_color, fg_color, state)
            elif isinstance(child, tk.Widget):
                self.style_tk_widget(child, bg_color, fg_color, state)

            # if isinstance(child, (ttk.Frame, tk.Frame)):
            #     child.configure(style='')
            #     if isinstance(child, ttk.Frame):
            #         self.style.configure('TFrame', background=bg_color)
            #     else:
            #         child.configure(bg=bg_colo
            if hasattr(child, 'winfo_children'):
                self.style_descendants(child, bg_color, fg_color, state)

    def style_tk_widget(self, widget, bg_color, fg_color, state):
        widget_class = widget.winfo_class()
        font_size = self.get_font_size(widget)
        if widget_class in ['Label', 'Button', 'Radiobutton', 'Checkbutton']:
            widget.configure(bg=bg_color, fg=fg_color, font=("TkDefaultFont", font_size))
        elif widget_class == 'Entry':
            widget.configure(bg=bg_color, fg=fg_color, insertbackground=fg_color, font=("TkDefaultFont", font_size))
        elif widget_class in ['Frame', 'Canvas']:
            widget.configure(bg=bg_color)
        elif widget_class == 'Listbox':
            listbox_bg = "#ffffff" if self.theme_var.get().lower() in ["clean", "retro"] and not self.dark_mode_var.get() else bg_color
            widget.configure(bg=listbox_bg, fg=fg_color, font=("TkDefaultFont", font_size))

    def style_ttk_widget(self, widget, bg_color, fg_color, state):
        widget_class = widget.winfo_class()
        theme = self.theme_var.get().lower()
        mode = "dark" if self.dark_mode_var.get() else "light"
        colors = DARK_COLORS[theme] if mode == "dark" else LIGHT_COLORS[theme]
        font_size = self.get_font_size(widget)

        if theme == "clean":
            if state == "Hover":
                bg_color = colors['hover_bg']
            elif state == "Click":
                bg_color = colors['click_bg']

        try:
            if widget_class in ['TLabel', 'TCheckbutton', 'TRadiobutton', 'TFrame', 'TLabelframe']:
                widget.configure(background=bg_color)
                if widget_class in ['TLabel', 'TCheckbutton', 'TRadiobutton']:
                    widget.configure(foreground=fg_color)
            elif widget_class in ['TEntry', 'TSpinbox', 'TCombobox']:
                widget.configure(fieldbackground=bg_color, foreground=fg_color)
            elif widget_class == 'TScale':
                widget.configure(troughcolor=bg_color)
            elif widget_class == 'TProgressbar':
                if theme == "retro":
                    widget.configure(background='blue', troughcolor='white' if mode == "light" else 'gray')
                else:
                    widget.configure(background=bg_color, troughcolor=bg_color)

            # Apply font size directly to widgets that support it
            if widget_class in ['TLabel', 'TCheckbutton', 'TRadiobutton', 'TEntry', 'TSpinbox', 'TCombobox']:
                widget.configure(font=("TkDefaultFont", font_size))

        except tk.TclError:
            pass  # Ignore if the widget doesn't support these options


    def get_font_size(self, widget):
        name = widget.winfo_name()
        font_match = re.search(r'font(\d+)', name)
        return int(font_match.group(1)) if font_match else 10  # default font size

    def is_mouse_within_bounds(self, x_root, y_root):
        left = self.outer_frame.winfo_rootx()
        right = left + self.outer_frame.winfo_width()
        top = self.outer_frame.winfo_rooty()
        bottom = top + self.outer_frame.winfo_height()
        return left <= x_root <= right and top <= y_root <= bottom

    def collect_widget_info(self):
        self.widget_info = {}
        for widget in self.surface.winfo_children():
            self._collect_widget_info_recursive(widget)

    def _collect_widget_info_recursive(self, widget):
        if isinstance(widget, tk.Listbox):
            selection = widget.curselection()
            if selection:
                self.widget_info[widget.winfo_name()] = widget.get(selection[0])
            else:
                self.widget_info[widget.winfo_name()] = "No selection"
        elif isinstance(widget, tk.Canvas):
            self.widget_info[widget.winfo_name()] = "Canvas clicked"
        elif hasattr(widget, 'get'):
            self.widget_info[widget.winfo_name()] = widget.get()
        elif isinstance(widget, ttk.Progressbar):
            self.widget_info[widget.winfo_name()] = widget.cget('value')
        elif isinstance(widget, ttk.Checkbutton):
            self.widget_info[widget.winfo_name()] = 'checked' if widget.instate(['selected']) else 'unchecked'
        
        if hasattr(widget, 'winfo_children'):
            for child in widget.winfo_children():
                self._collect_widget_info_recursive(child)

    def recreate(self):
            grid_info = self.outer_frame.grid_info()
            self.outer_frame.destroy()
            self.__init__(self.parent, self.create_surface, self.theme_var, self.dark_mode_var, self.command)
            self.outer_frame.grid(**grid_info)

class MouseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("MouseTracker")
        self.root.geometry("160x165")
        self.root.minsize(160, 165)

        self.tracking_mouse = False
        self.mouse_position_after_id = None
        
        self.theme_var = tk.StringVar(value="Clean")
        self.dark_mode_var = tk.BooleanVar(value=False)

        self.style=ttk.Style()
        self.style.theme_use("xpnative")

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(expand=False, padx=5, pady=5)

        self.tracker_button = FancyButton(self.main_frame, self.create_mouse_tracker_surface, self.theme_var, self.dark_mode_var, self.toggle_mouse_tracking)
        self.tracker_button.outer_frame.grid(row=0, column=0, padx=5, pady=5)  # Add this line
        
        self.cancel_button = ttk.Button(self.main_frame, text="Cancel", width=8, command=self.root.quit)
        self.cancel_button.grid(row=1, column=0, padx=5, pady=5)


    def create_mouse_tracker_surface(self, surface):
        self.mt_title = ttk.Label(surface, text="Mouse Tracker", anchor="center", width=12, name="mt_title_font12")
        self.mt_title.pack(fill=tk.BOTH, padx=5, pady=5)
        ttk.Separator(surface, orient="horizontal").pack(fill=tk.X, padx=5, pady=0)
        self.mt_coordinates = ttk.Label(surface, text="Pixel:          (0, 0)\nWindows:  (0, 0)", anchor="w", name="mt_coordinates_font8")
        self.mt_coordinates.pack(fill=tk.X, padx=10, pady=2)
        self.mt_start = ttk.Label(surface, text="Start Tracking", anchor="center", name="mt_start_font10")
        self.mt_start.pack(fill=tk.BOTH, padx=5, pady=5, ipady=5)
        return surface.winfo_children()


    # Included a mouse x-y tracker
    def mouse_position(self):
        x_m, y_m = pyautogui.position() #get coordinates from pyautogui
        
        # Use windows offset to display the coordinate according to Windows

        # SET win_offset ABOVE!

        x_w = x_m - win_offset_x
        y_w = y_m - win_offset_y

        self.mt_coordinates.config(text=f"Pixel:          ({x_m},{y_m})\nWindows:  ({x_w},{y_w})")
        # Reschedule the mouse_position method and store the task ID
        self.mouse_position_after_id = self.root.after(100, self.mouse_position)
    
    def toggle_mouse_tracking(self):
        self.tracking_mouse = not self.tracking_mouse  # Toggle the state

    def toggle_mouse_tracking(self):
        self.tracking_mouse = not self.tracking_mouse
        
        if self.tracking_mouse:
            self.mt_start.config(text="Stop Tracking")
            self.mouse_position()
        else:
            self.mt_start.config(text="Start Tracking")
            if self.mouse_position_after_id:
                self.root.after_cancel(self.mouse_position_after_id)
                self.mouse_position_after_id = None



if __name__ == "__main__":
    
    root = tk.Tk()
    app = MouseTracker(root)

    root.mainloop()