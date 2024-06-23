# -*- coding: utf-8 -*-
"""
Created on Sat Jun 15 17:55:55 2024

@author: Thomas
"""

# TASK MANAGER BUTTON TEST APP

# Fancybutton class takes a surface defined with ttk objects, places it in a series of tk frames and applies styling to give the appearance and functionality of a regular button

"""
Description:
This script creates a Tkinter application to test a custom FancyButton widget 
that can toggle between 'Clean' and 'Retro' themes. The FancyButton updates 
its style based on mouse events (hover, click) and the selected theme.

Usage:
- Run this script using Python 3. The script creates a window with a 
  toggle button to switch between 'Clean' and 'Retro' themes.
- The application includes a 'Task Manager' button implemented using 
  the FancyButton class, which changes its appearance based on the theme and 
  mouse events.
- The script also includes a test frame with a label to compare the relief 
  appearance against the FancyButton.

Requirements:
- Python 3
- Tkinter library (usually included with Python standard library)
- Windows OS (for the 'taskmgr' functionality to work)

How to Use:
1. Run the script: python test4.py
2. Click the 'Toggle Theme' button to switch between 'Clean' and 'Retro' themes.
3. Observe the changes in the 'Task Manager' button appearance and the relief 
   effect on the test frame.
4. Click the 'Task Manager' button to open the Windows Task Manager.

Additional Notes:
- The FancyButton class relies on ttk styles for text formatting and appearance. 
  Ensure that any text widgets inside the FancyButton's surface frame use the 
  defined styles.
- The class is designed to switch between 'Clean' and 'Retro' themes. If you 
  need more themes or different behaviors, update the define_styles and 
  update_style methods accordingly.
- Mouse events are handled for the button and its child widgets. If you add 
  more widgets, ensure they are bound to the necessary events.
- The task_manager_click method is Windows-specific. Modify it for cross-platform 
  compatibility if needed.
- The recreate method reinitializes the button to apply new theme settings. Ensure 
  your application logic calls this method when changing themes.


"""







import tkinter as tk
from tkinter import ttk
import subprocess









class FancyButton:
    def __init__(self, parent, create_surface, theme_var, command):
        self.parent = parent
        self.create_surface = create_surface  # Store create_surface function
        self.theme_var = theme_var
        self.command = command

        self.style = ttk.Style()
        self.define_styles()

        # Create outer frame with no border initially
        self.outer_frame = tk.Frame(self.parent, bd=0, highlightthickness=0)
        self.outer_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

        # Create inner frame inside the outer frame
        self.inner_frame = tk.Frame(self.outer_frame, bd=0, highlightthickness=0)
        self.inner_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # Create surface frame inside the inner frame
        self.surface = tk.Frame(self.inner_frame, bd=0, highlightthickness=0)
        self.surface.pack(fill=tk.BOTH, expand=False, padx=0, pady=0)

        self.create_surface(self.surface)

        self.is_hovered = False
        self.bind_events()
        self.update_style("")  # Ensure initial style is applied

    def define_styles(self):
        task_title = ("", 8)
        label_font = ("", 6)

        # Colors
        self.clean_label_bg = "#e1e1e1"
        self.clean_hover_bg = "#e5f1fb"
        self.clean_click_bg = "#cce4f7"
        self.clean_border_color = "#adadad"
        self.clean_hover_border = "#0078d7"
        self.clean_click_border = "#005499"

        self.retro_label_bg = "#f0f0f0"
        self.retro_hover_bg = "#f0f0f0"
        self.retro_click_bg = "#f0f0f0"

        # Clean theme styles
        self.style.configure("cleanFrameButtonSurface.TFrame", background=self.clean_label_bg, relief="solid", borderwidth=0)
        self.style.configure("cleanFrameButtonHoverSurface.TFrame", background=self.clean_hover_bg, relief="solid", borderwidth=0)
        self.style.configure("cleanFrameButtonClickSurface.TFrame", background=self.clean_click_bg, relief="solid", borderwidth=0)
        self.style.configure("cleanFrameButton.TLabel", background=self.clean_label_bg, font=task_title)
        self.style.configure("cleanFrameButtonHover.TLabel", background=self.clean_hover_bg, font=task_title)
        self.style.configure("cleanFrameButtonClick.TLabel", background=self.clean_click_bg, font=task_title)
        self.style.configure("cleanFrameButtonText.TLabel", background=self.clean_label_bg, font=label_font)
        self.style.configure("cleanFrameButtonHoverText.TLabel", background=self.clean_hover_bg, font=label_font)
        self.style.configure("cleanFrameButtonClickText.TLabel", background=self.clean_click_bg, font=label_font)

        # Retro theme styles
        self.style.configure("retroFrameButtonSurface.TFrame", background=self.retro_label_bg, relief="flat", borderwidth=0)
        self.style.configure("retroFrameButtonHoverSurface.TFrame", background=self.retro_hover_bg, relief="flat", borderwidth=0)
        self.style.configure("retroFrameButtonClickSurface.TFrame", background=self.retro_click_bg, relief="flat", borderwidth=0)
        self.style.configure("retroFrameButton.TLabel", background=self.retro_label_bg, font=task_title)
        self.style.configure("retroFrameButtonHover.TLabel", background=self.retro_hover_bg, font=task_title)
        self.style.configure("retroFrameButtonClick.TLabel", background=self.retro_click_bg, font=task_title)
        self.style.configure("retroFrameButtonText.TLabel", background=self.retro_label_bg, font=label_font)
        self.style.configure("retroFrameButtonHoverText.TLabel", background=self.retro_hover_bg, font=label_font)
        self.style.configure("retroFrameButtonClickText.TLabel", background=self.retro_click_bg, font=label_font)

    def bind_events(self):
        self.outer_frame.bind("<Enter>", self.on_enter)
        self.outer_frame.bind("<Leave>", self.on_leave)
        self.surface.bind("<Enter>", self.on_enter_child)
        self.surface.bind("<Leave>", self.on_leave_child)
        self.outer_frame.bind("<Button-1>", self.on_click)
        self.outer_frame.bind("<ButtonRelease-1>", self.on_release)
        self.bind_children(self.surface)

    def bind_children(self, widget):
        widget.bind("<Enter>", self.on_enter_child)
        widget.bind("<Leave>", self.on_leave_child)
        widget.bind("<Button-1>", self.on_click)
        widget.bind("<ButtonRelease-1>", self.on_release)
        for child in widget.winfo_children():
            self.bind_children(child)

    def on_enter(self, event):
        self.update_style("Hover")
        self.is_hovered = True

    def on_leave(self, event):
        self.is_hovered = False
        self.update_style("")

    def on_enter_child(self, event):
        self.is_hovered = True

    def on_leave_child(self, event):
        if not self.is_mouse_within_bounds(event.x_root, event.y_root):
            self.update_style("")
            self.is_hovered = False

    def on_click(self, event):
        self.update_style("Click")

    def on_release(self, event):
        if self.is_mouse_within_bounds(event.x_root, event.y_root):
            self.command()
        self.update_style("Hover" if self.is_mouse_within_bounds(event.x_root, event.y_root) else "")

    def update_style(self, state):
        theme = self.theme_var.get().lower()
        surface_style = f"{theme}FrameButton{state}Surface.TFrame"
        label_style = f"{theme}FrameButton{state}.TLabel"
        text_style = f"{theme}FrameButton{state}Text.TLabel"

        if theme == "clean":
            if state == "Hover":
                self.outer_frame.config(bg=self.clean_hover_border, bd=0)
                self.inner_frame.config(bg=self.clean_hover_bg)
            elif state == "Click":
                self.outer_frame.config(bg=self.clean_click_border, bd=0)
                self.inner_frame.config(bg=self.clean_click_bg)
            else:
                self.outer_frame.config(bg=self.clean_border_color, bd=0)
                self.inner_frame.config(bg=self.clean_label_bg)
        elif theme == "retro":
            if state == "Hover":
                self.outer_frame.config(bd=2, relief="raised")  # Apply raised relief on hover
                self.inner_frame.config(bg=self.retro_hover_bg)
            elif state == "Click":
                self.outer_frame.config(bd=2, relief="sunken")  # Apply sunken relief on click
                self.inner_frame.config(bg=self.retro_click_bg)
            else:
                self.outer_frame.config(bd=2, relief="raised")  # Default to raised relief
                self.inner_frame.config(bg=self.retro_label_bg)

        # Set the background color of the surface to match the inner frame
        self.surface.config(bg=self.inner_frame.cget("bg"))

        # Apply styles to labels
        for widget in self.surface.winfo_children():
            if isinstance(widget, ttk.Label):
                widget.configure(style=label_style if widget.cget("text") == "Task Manager" else text_style)

        # Update the frames to apply changes
        self.outer_frame.update_idletasks()
        self.inner_frame.update_idletasks()
        self.surface.update_idletasks()

    def is_mouse_within_bounds(self, x_root, y_root):
        left = self.outer_frame.winfo_rootx()
        right = self.outer_frame.winfo_rootx() + self.outer_frame.winfo_width()
        top = self.outer_frame.winfo_rooty()
        bottom = self.outer_frame.winfo_rooty() + self.outer_frame.winfo_height()
        return left <= x_root <= right and top <= y_root <= bottom

    def recreate(self):
        self.outer_frame.destroy()
        self.__init__(self.parent, self.create_surface, self.theme_var, self.command)

class TMBtestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Taskmanager Button Tester App")
        self.root.geometry("400x300")

        self.style = ttk.Style()
        self.theme_var = tk.StringVar(value="Clean")
        self.style.theme_use('xpnative')

        main_frame = ttk.Frame(root)
        main_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.toolbox_frame = ttk.Frame(main_frame)
        self.toolbox_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.taskmanager_button = FancyButton(self.toolbox_frame, self.create_button_surface, self.theme_var, self.task_manager_click)

        self.test_frame = tk.Frame(main_frame, bd=2, relief="raised")
        self.test_frame.grid(row=1, column=0, padx=5, pady=5)
        self.test_label = tk.Label(self.test_frame, text="Test Label\nin a\nTest Frame", font=("", 8))
        self.test_label.pack()

        self.toggle_theme_button = ttk.Button(main_frame, text="Toggle Theme", command=self.toggle_theme)
        self.toggle_theme_button.grid(row=2, column=0, padx=20, pady=20)

    def create_button_surface(self, parent):
        ttk.Label(parent, text="Task Manager", style="cleanFrameButton.TLabel", anchor="center", width=12).pack(fill=tk.X, padx=5, pady=(2, 0))
        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, padx=5, pady=0)
        ttk.Label(parent, text="CPU:  0%", style="cleanFrameButtonText.TLabel", anchor="w").pack(fill=tk.X, padx=10, pady=(0, 0))
        ttk.Label(parent, text="RAM:  0%", style="cleanFrameButtonText.TLabel", anchor="w").pack(fill=tk.X, padx=10, pady=0)
        ttk.Label(parent, text="DISK: 0%", style="cleanFrameButtonText.TLabel", anchor="w").pack(fill=tk.X, padx=10, pady=0)
        ttk.Label(parent, text="UP:   0 MB", style="cleanFrameButtonText.TLabel", anchor="w").pack(fill=tk.X, padx=10, pady=0)
        ttk.Label(parent, text="DOWN: 0 MB", style="cleanFrameButtonText.TLabel", anchor="w").pack(fill=tk.X, padx=10, pady=(0, 2))

    def toggle_theme(self):
        if self.theme_var.get() == "Clean":
            self.theme_var.set("Retro")
            self.style.theme_use('winnative')
        else:
            self.theme_var.set("Clean")
            self.style.theme_use('xpnative')
        self.taskmanager_button.recreate()
        self.reset_test_frame()

    def reset_test_frame(self):
        self.test_frame.config(relief="raised", bd=2)
        self.test_label.config(font=("", 8))

    def task_manager_click(self):
        print("Task Manager Clicked")
        subprocess.Popen(["powershell", "-Command", "Start-Process taskmgr -Verb runAs"])

if __name__ == "__main__":
    root = tk.Tk()
    app = TMBtestApp(root)
    root.mainloop()
