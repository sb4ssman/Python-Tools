# Task button tester



import tkinter as tk
from tkinter import ttk
import subprocess

class ToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Taskmanager Button Tester App")
        self.root.geometry("400x300")

        self.style = ttk.Style()

        self.theme_var = tk.StringVar(value="Clean")
        self.style.theme_use('xpnative')

        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.toolbox_frame = ttk.Frame(main_frame)
        self.toolbox_frame.pack(expand=False)

        self.create_task_manager_button()

        self.button = ttk.Button(main_frame, text="Toggle Theme", command=self.toggle_theme)
        self.button.pack(padx=5, pady=10)

    # Task Manager Button
    def create_task_manager_button(self):
        task_title = ("", 8)
        label_font = ("", 6)

        # Define styles based on the current theme
        if self.theme_var.get() == "Clean":
            label_bg = "#e1e1e1"  # Background color of normal buttons (a light gray)
            hover_bg = "#e5f1fb"  # Background color on hover (a light blue)
            click_bg = "#cce4f7"  # Background color on click (a slightly darker light-blue)
            border_color = "#adadad"  # Normal border color (A darker gray)
            hover_border = "#0078d7"  # Border color on hover (a royal blue)
            click_border = "#005499"  # Border color on click (slightly darker royal blue)

            # Normal button state
            self.style.configure("TaskManagerFrame.TFrame", background=border_color, relief="solid", borderwidth=1)  # Outer Frame
            self.style.configure("TaskManagerSurface.TFrame", background=label_bg, relief="solid", borderwidth=0)  # Inner frame
            self.style.configure("TaskManagerTitle.TLabel", background=label_bg, font=task_title)
            self.style.configure("TaskManagerText.TLabel", background=label_bg, font=label_font)

            # Hover state
            self.style.configure("TaskManagerFrameHover.TFrame", background=hover_border, relief="solid", borderwidth=1)  # Outer Frame
            self.style.configure("TaskManagerSurfaceHover.TFrame", background=hover_bg, relief="solid", borderwidth=0)  # Inner frame
            self.style.configure("TaskManagerTitleHover.TLabel", background=hover_bg, font=task_title)
            self.style.configure("TaskManagerTextHover.TLabel", background=hover_bg, font=label_font)

            # Click state
            self.style.configure("TaskManagerFrameClick.TFrame", background=click_border, relief="solid", borderwidth=1)  # Outer Frame
            self.style.configure("TaskManagerSurfaceClick.TFrame", background=click_bg, relief="solid", borderwidth=0)  # Inner frame
            self.style.configure("TaskManagerTitleClick.TLabel", background=click_bg, font=task_title)
            self.style.configure("TaskManagerTextClick.TLabel", background=click_bg, font=label_font)

        elif self.theme_var.get() == "Retro":
            label_bg = "#f0f0f0"
            border_color = "#d4d0c8"

            self.style.configure("TaskManagerFrame.TFrame", background=border_color, relief="raised", borderwidth=1)  # Outer Frame
            self.style.configure("TaskManagerSurface.TFrame", background=label_bg, relief="solid", borderwidth=0)  # Inner frame
            self.style.configure("TaskManagerTitle.TLabel", background=label_bg, font=task_title)
            self.style.configure("TaskManagerText.TLabel", background=label_bg, font=label_font)

        # Custom frame for border color
        self.taskmanager_border_frame = tk.Frame(self.toolbox_frame, bg=border_color, highlightbackground=border_color, highlightthickness=1)
        self.taskmanager_border_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

        self.taskmanager_label_frame = tk.Frame(self.taskmanager_border_frame, bg=label_bg)
        self.taskmanager_label_frame.pack(fill=tk.BOTH, expand=False, padx=0, pady=0)

        # Task Manager Label with underline
        self.taskmanager_label = ttk.Label(self.taskmanager_label_frame, text="Task Manager", style="TaskManagerTitle.TLabel", anchor="center", width=11)
        self.taskmanager_label.pack(fill=tk.X, padx=5, pady=(2, 0))

        # Adding separator for additional styling
        self.separator = ttk.Separator(self.taskmanager_label_frame, orient="horizontal")
        self.separator.pack(fill=tk.X, padx=5, pady=2)

        # The labels
        self.cpu_usage_label = ttk.Label(self.taskmanager_label_frame, text="CPU:  0%", style="TaskManagerText.TLabel", anchor="w")
        self.cpu_usage_label.pack(fill=tk.X, padx=10, pady=(5, 0))

        self.ram_usage_label = ttk.Label(self.taskmanager_label_frame, text="RAM:  0%", style="TaskManagerText.TLabel", anchor="w")
        self.ram_usage_label.pack(fill=tk.X, padx=10, pady=0)

        self.disk_usage_label = ttk.Label(self.taskmanager_label_frame, text="DISK: 0%", style="TaskManagerText.TLabel", anchor="w")
        self.disk_usage_label.pack(fill=tk.X, padx=10, pady=0)

        self.netsend_usage_label = ttk.Label(self.taskmanager_label_frame, text="UP:   0 MB", style="TaskManagerText.TLabel", anchor="w")
        self.netsend_usage_label.pack(fill=tk.X, padx=10, pady=0)

        self.netrecv_usage_label = ttk.Label(self.taskmanager_label_frame, text="DOWN: 0 MB", style="TaskManagerText.TLabel", anchor="w")
        self.netrecv_usage_label.pack(fill=tk.X, padx=10, pady=0)

        # Bind click and hover events
        self.taskmanager_label_frame.bind("<Button-1>", self.task_manager_click)  # This makes it behave like a button
        self.bind_children(self.taskmanager_label_frame, lambda event: self.task_manager_click())  # and all the children too

        if self.theme_var.get() == "Clean":
            self.taskmanager_label_frame.bind("<Enter>", lambda e: self.on_enter_taskmanager_frame(self.taskmanager_border_frame, self.taskmanager_label_frame, hover_border, hover_bg))
            self.taskmanager_label_frame.bind("<Leave>", lambda e: self.on_leave_taskmanager_frame(self.taskmanager_border_frame, self.taskmanager_label_frame, border_color, label_bg))
            self.taskmanager_label_frame.bind("<ButtonPress-1>", lambda e: self.on_click_taskmanager_frame(self.taskmanager_border_frame, self.taskmanager_label_frame, click_border, click_bg))
            self.taskmanager_label_frame.bind("<ButtonRelease-1>", lambda e: self.on_release_taskmanager_frame(self.taskmanager_border_frame, self.taskmanager_label_frame, border_color, label_bg))
        elif self.theme_var.get() == "Retro":
            self.taskmanager_label_frame.bind("<ButtonPress-1>", lambda e: self.on_click_taskmanager_frame_retro(self.taskmanager_border_frame))
            self.taskmanager_label_frame.bind("<ButtonRelease-1>", lambda e: self.on_release_taskmanager_frame_retro(self.taskmanager_border_frame))

    def bind_children(self, widget, callback):
        widget.bind("<Button-1>", callback)
        for child in widget.winfo_children():
            self.bind_children(child, callback)

    def on_enter_taskmanager_frame(self, outer_frame, inner_frame, hover_border, hover_bg):
        print("Hover enter")
        outer_frame.config(highlightbackground=hover_border)
        inner_frame.config(bg=hover_bg)
        for widget in inner_frame.winfo_children():
            if isinstance(widget, ttk.Label):
                if widget.cget("text") == "Task Manager":
                    widget.config(style="TaskManagerTitleHover.TLabel")
                else:
                    widget.config(style="TaskManagerTextHover.TLabel")

    def on_leave_taskmanager_frame(self, outer_frame, inner_frame, border_color, label_bg):
        print("Hover leave")
        outer_frame.config(highlightbackground=border_color)
        inner_frame.config(bg=label_bg)
        for widget in inner_frame.winfo_children():
            if isinstance(widget, ttk.Label):
                if widget.cget("text") == "Task Manager":
                    widget.config(style="TaskManagerTitle.TLabel")
                else:
                    widget.config(style="TaskManagerText.TLabel")

    def on_click_taskmanager_frame(self, outer_frame, inner_frame, click_border, click_bg):
        print("Click detected")
        outer_frame.config(highlightbackground=click_border)
        inner_frame.config(bg=click_bg)
        for widget in inner_frame.winfo_children():
            if isinstance(widget, ttk.Label):
                if widget.cget("text") == "Task Manager":
                    widget.config(style="TaskManagerTitleClick.TLabel")
                else:
                    widget.config(style="TaskManagerTextClick.TLabel")

    def on_release_taskmanager_frame(self, outer_frame, inner_frame, border_color, label_bg):
        print("Release detected")
        outer_frame.config(highlightbackground=border_color)
        inner_frame.config(bg=label_bg)
        for widget in inner_frame.winfo_children():
            if isinstance(widget, ttk.Label):
                if widget.cget("text") == "Task Manager":
                    widget.config(style="TaskManagerTitle.TLabel")
                else:
                    widget.config(style="TaskManagerText.TLabel")

    def on_click_taskmanager_frame_retro(self, frame):
        print("Click detected (Retro)")
        frame.config(relief="sunken")

    def on_release_taskmanager_frame_retro(self, frame):
        print("Release detected (Retro)")
        frame.config(relief="raised")

    def toggle_theme(self):
        if self.theme_var.get() == "Clean":
            self.theme_var.set(value="Retro")
            self.style.theme_use('winnative')
        else:
            self.theme_var.set(value="Clean")
            self.style.theme_use('xpnative')

    def task_manager_click(self):
        subprocess.Popen(["powershell", "-Command", "Start-Process taskmgr -Verb runAs"])


if __name__ == "__main__":
    root = tk.Tk()
    app = ToolApp(root)
    root.mainloop()
