import tkinter as tk
from tkinter import ttk
import subprocess

class StyleManager:
    def __init__(self):
        self.styles = {}
        self.current_theme = "clean"
        self.define_styles()

    def define_styles(self):
        task_title = ("", 8)
        label_font = ("", 6)

        # Clean theme styles
        self.styles["clean"] = {
            "Frame": {"background": "#e1e1e1", "borderwidth": 0},
            "HoverFrame": {"background": "#e5f1fb", "borderwidth": 0},
            "ClickFrame": {"background": "#cce4f7", "borderwidth": 0},
            "Label": {"background": "#e1e1e1", "font": task_title},
            "HoverLabel": {"background": "#e5f1fb", "font": task_title},
            "ClickLabel": {"background": "#cce4f7", "font": task_title},
            "TextLabel": {"background": "#e1e1e1", "font": label_font},
            "HoverTextLabel": {"background": "#e5f1fb", "font": label_font},
            "ClickTextLabel": {"background": "#cce4f7", "font": label_font}
        }

        # Retro theme styles
        self.styles["retro"] = {
            "Frame": {"background": "#f0f0f0", "borderwidth": 1, "relief": "raised"},
            "HoverFrame": {"background": "#f0f0f0", "borderwidth": 1, "relief": "raised"},
            "ClickFrame": {"background": "#f0f0f0", "borderwidth": 1, "relief": "sunken"},
            "Label": {"background": "#f0f0f0", "font": task_title},
            "HoverLabel": {"background": "#f0f0f0", "font": task_title},
            "ClickLabel": {"background": "#f0f0f0", "font": task_title},
            "TextLabel": {"background": "#f0f0f0", "font": label_font},
            "HoverTextLabel": {"background": "#f0f0f0", "font": label_font},
            "ClickTextLabel": {"background": "#f0f0f0", "font": label_font}
        }

    def apply_style(self, widget, style_name):
        style = self.styles[self.current_theme][style_name]
        widget.configure(**style)

    def set_theme(self, theme):
        self.current_theme = theme

class FancyButton:
    def __init__(self, parent, style_manager, create_surface, theme_var, command, font_size=1):
        self.parent = parent
        self.style_manager = style_manager
        self.theme_var = theme_var
        self.command = command
        self.font_size = font_size

        self.outer_frame = tk.Frame(self.parent, bd=0, highlightthickness=0)
        self.inner_frame = tk.Frame(self.outer_frame, bd=0, highlightthickness=0)
        self.surface = tk.Frame(self.inner_frame, bd=0, highlightthickness=0)

        self.style_manager.apply_style(self.outer_frame, "Frame")
        self.style_manager.apply_style(self.inner_frame, "Frame")
        self.style_manager.apply_style(self.surface, "Frame")

        self.outer_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        self.inner_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        self.surface.pack(fill=tk.BOTH, expand=False, padx=0, pady=0)

        create_surface(self.surface)

        self.is_hovered = False
        self.bind_events()
        self.update_style("")  # Ensure initial style is applied

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
        frame_style = f"{state}Frame" if state else "Frame"
        label_style = f"{state}Label" if state else "Label"
        text_style = f"{state}TextLabel" if state else "TextLabel"

        self.style_manager.apply_style(self.outer_frame, frame_style)
        self.style_manager.apply_style(self.inner_frame, frame_style)
        self.style_manager.apply_style(self.surface, frame_style)

        for widget in self.surface.winfo_children():
            if isinstance(widget, ttk.Label):
                widget_text = widget.cget("text")
                if widget_text == "Task Manager":
                    self.style_manager.apply_style(widget, label_style)
                else:
                    self.style_manager.apply_style(widget, text_style)

    def is_mouse_within_bounds(self, x_root, y_root):
        left = self.outer_frame.winfo_rootx()
        right = self.outer_frame.winfo_rootx() + self.outer_frame.winfo_width()
        top = self.outer_frame.winfo_rooty()
        bottom = self.outer_frame.winfo_rooty() + self.outer_frame.winfo_height()
        return left <= x_root <= right and top <= y_root <= bottom

class FancyButtonTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fancy Button Tester App")
        self.root.geometry("400x600")

        self.style_manager = StyleManager()
        self.theme_var = tk.StringVar(value="clean")

        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.toolbox_frame = ttk.Frame(main_frame)
        self.toolbox_frame.grid_columnconfigure(0, weight=1)
        self.toolbox_frame.grid_columnconfigure(1, weight=1)
        self.toolbox_frame.grid_columnconfigure(2, weight=1)
        self.toolbox_frame.grid_rowconfigure(0, weight=1)
        self.toolbox_frame.grid_rowconfigure(1, weight=1)
        self.toolbox_frame.pack(expand=False, fill=tk.BOTH)

        self.mouse_tracker_button = FancyButton(self.toolbox_frame, self.style_manager, self.create_mouse_tracker_surface, self.theme_var, self.toggle_mouse_tracking, font_size=2)
        self.mouse_tracker_button.outer_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.prompt_button = FancyButton(self.toolbox_frame, self.style_manager, self.create_prompt_surface, self.theme_var, self.open_prompt_dropdown, font_size=1)
        self.prompt_button.outer_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        self.taskmanager_button = FancyButton(self.toolbox_frame, self.style_manager, self.create_taskmanager_surface, self.theme_var, self.task_manager_click, font_size=0)
        self.taskmanager_button.outer_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")

        self.spinbox_button = FancyButton(self.toolbox_frame, self.style_manager, self.create_spinbox_surface, self.theme_var, self.sample_function_spinbox, font_size=1)
        self.spinbox_button.outer_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        self.radiobutton_button = FancyButton(self.toolbox_frame, self.style_manager, self.create_radiobutton_surface, self.theme_var, self.sample_function_radiobutton, font_size=2)
        self.radiobutton_button.outer_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        self.scale_button = FancyButton(self.toolbox_frame, self.style_manager, self.create_scale_surface, self.theme_var, self.sample_function_scale, font_size=0)
        self.scale_button.outer_frame.grid(row=1, column=2, padx=5, pady=5, sticky="nsew")

        self.listbox_button = FancyButton(self.toolbox_frame, self.style_manager, self.create_listbox_surface, self.theme_var, self.sample_function_listbox, font_size=1)
        self.listbox_button.outer_frame.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")

        self.canvas_button = FancyButton(self.toolbox_frame, self.style_manager, self.create_canvas_surface, self.theme_var, self.sample_function_canvas, font_size=2)
        self.canvas_button.outer_frame.grid(row=2, column=1, padx=5, pady=5, sticky="nsew")

        self.progressbar_button = FancyButton(self.toolbox_frame, self.style_manager, self.create_progressbar_surface, self.theme_var, self.sample_function_progressbar, font_size=0)
        self.progressbar_button.outer_frame.grid(row=2, column=2, padx=5, pady=5, sticky="nsew")

        self.toggle_theme_button = ttk.Button(main_frame, text="Toggle Theme", command=self.toggle_theme)
        self.toggle_theme_button.pack(padx=5, pady=10)

    def create_taskmanager_surface(self, parent):
        ttk.Label(parent, text="Task Manager", anchor="center", width=12).pack(fill=tk.X, padx=5, pady=(2, 0))
        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, padx=5, pady=0)
        ttk.Label(parent, text="CPU:  0%", anchor="w").pack(fill=tk.X, padx=10, pady=(0, 0))
        ttk.Label(parent, text="RAM:  0%", anchor="w").pack(fill=tk.X, padx=10, pady=0)
        ttk.Label(parent, text="DISK: 0%", anchor="w").pack(fill=tk.X, padx=10, pady=0)
        ttk.Label(parent, text="UP:   0 MB", anchor="w").pack(fill=tk.X, padx=10, pady=0)
        ttk.Label(parent, text="DOWN: 0 MB", anchor="w").pack(fill=tk.X, padx=10, pady=(0, 2))

    def create_prompt_surface(self, parent):
        ttk.Label(parent, text="Prompt Chooser", anchor="center", width=12).pack(fill=tk.X, padx=5, pady=(2, 0))
        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, padx=5, pady=0)
        ttk.Combobox(parent, textvariable=tk.StringVar(value="Terminal"), values=["Terminal", "PowerShell", "cmd"], state="readonly", width=10).pack(fill=tk.X, padx=5, pady=5)
        ttk.Checkbutton(parent, text="Admin", variable=tk.IntVar()).pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(parent, text="Prompt", anchor="center", width=12).pack(fill=tk.BOTH, padx=5, pady=5, ipady=5)

    def create_mouse_tracker_surface(self, parent):
        ttk.Label(parent, text="Mouse Tracker", anchor="center", width=12).pack(fill=tk.X, padx=5, pady=(2, 0))
        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, padx=5, pady=0)
        ttk.Label(parent, text="Pixel:          (0, 0)\nWindows:  (0, 0)", anchor="w").pack(fill=tk.X, padx=10, pady=2)
        ttk.Label(parent, text="Start Tracking", anchor="center", width=12).pack(fill=tk.BOTH, padx=5, pady=5, ipady=5)

    def create_spinbox_surface(self, parent):
        ttk.Label(parent, text="Spinbox", anchor="center", width=12).pack(fill=tk.X, padx=5, pady=(2, 0))
        ttk.Spinbox(parent, from_=0, to=10, width=6).pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(parent, text="Font Size 6", anchor="center", width=12).pack(fill=tk.X, padx=5, pady=(2, 0))

    def create_radiobutton_surface(self, parent):
        ttk.Label(parent, text="Radiobutton", anchor="center", width=12).pack(fill=tk.X, padx=5, pady=(2, 0))
        radio_var = tk.StringVar()
        ttk.Radiobutton(parent, text="Option 1", variable=radio_var, value="Option 1").pack(fill=tk.X, padx=5, pady=5)
        ttk.Radiobutton(parent, text="Option 2", variable=radio_var, value="Option 2").pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(parent, text="Font Size 6", anchor="center", width=12).pack(fill=tk.X, padx=5, pady=(2, 0))

    def create_scale_surface(self, parent):
        ttk.Label(parent, text="Scale", anchor="center", width=12).pack(fill=tk.X, padx=5, pady=(2, 0))
        ttk.Scale(parent, from_=0, to=100).pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(parent, text="Font Size 6", anchor="center", width=12).pack(fill=tk.X, padx=5, pady=(2, 0))

    def create_listbox_surface(self, parent):
        ttk.Label(parent, text="Listbox", anchor="center", width=12).pack(fill=tk.X, padx=5, pady=(2, 0))
        listbox = tk.Listbox(parent, width=10, height=5)
        listbox.pack(fill=tk.X, padx=5, pady=5)
        for i in range(1, 11):
            listbox.insert(tk.END, f"Item {i}")
        ttk.Label(parent, text="Font Size 6", anchor="center", width=12).pack(fill=tk.X, padx=5, pady=(2, 0))

    def create_canvas_surface(self, parent):
        ttk.Label(parent, text="Canvas", anchor="center", width=12).pack(fill=tk.X, padx=5, pady=(2, 0))
        canvas = tk.Canvas(parent, width=100, height=50, bg="white")
        canvas.pack(fill=tk.X, padx=5, pady=5)
        canvas.create_oval(10, 10, 90, 40, fill="blue")
        ttk.Label(parent, text="Font Size 6", anchor="center", width=12).pack(fill=tk.X, padx=5, pady=(2, 0))

    def create_progressbar_surface(self, parent):
        ttk.Label(parent, text="Progressbar", anchor="center", width=12).pack(fill=tk.X, padx=5, pady=(2, 0))
        ttk.Progressbar(parent, value=50).pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(parent, text="Font Size 6", anchor="center", width=12).pack(fill=tk.X, padx=5, pady=(2, 0))

    def toggle_theme(self):
        if self.theme_var.get() == "clean":
            self.theme_var.set("retro")
        else:
            self.theme_var.set("clean")
        self.style_manager.set_theme(self.theme_var.get())
        self.taskmanager_button.update_style("")
        self.mouse_tracker_button.update_style("")
        self.prompt_button.update_style("")
        self.spinbox_button.update_style("")
        self.radiobutton_button.update_style("")
        self.scale_button.update_style("")
        self.listbox_button.update_style("")
        self.canvas_button.update_style("")
        self.progressbar_button.update_style("")

    def task_manager_click(self):
        print("Task Manager Clicked")
        subprocess.Popen(["powershell", "-Command", "Start-Process taskmgr -Verb runAs"])

    def open_prompt_dropdown(self):
        selected_prompt = "Terminal"  # For demo purpose
        print(f"Opening prompt dropdown: {selected_prompt}")

    def toggle_mouse_tracking(self):
        print("Toggling mouse tracking")

    def sample_function_spinbox(self):
        value = "5"  # For demo purpose
        print(f"Spinbox value: {value}")

    def sample_function_radiobutton(self):
        selected_option = "Option 1"  # For demo purpose
        print(f"Selected radiobutton: {selected_option}")

    def sample_function_scale(self):
        value = 50  # For demo purpose
        print(f"Scale value: {value}")

    def sample_function_listbox(self):
        selected_items = ["Item 1"]  # For demo purpose
        print(f"Selected listbox items: {selected_items}")

    def sample_function_canvas(self):
        print("Canvas clicked")

    def sample_function_progressbar(self):
        value = 50  # For demo purpose
        print(f"Progressbar value: {value}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FancyButtonTestApp(root)
    root.mainloop()
