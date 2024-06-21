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

        self.outer_frame = tk.Frame(self.parent, bd=0, highlightthickness=0)
        self.outer_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

        self.inner_frame = tk.Frame(self.outer_frame, bd=0, highlightthickness=0)
        self.inner_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        self.surface = tk.Frame(self.inner_frame, bd=0, highlightthickness=0)
        self.surface.pack(fill=tk.BOTH, expand=False, padx=0, pady=0)

        self.create_surface(self.surface)

        self.is_hovered = False
        self.bind_events()
        self.update_style("")  # Ensure initial style is applied

    def define_styles(self):
        # Define font sizes
        self.font_pairs = {
            'font12': ("", 12),
            'font10': ("", 10),
            'font8': ("", 8),
            'font6': ("", 6)
        }

        # Colors
        self.clean_label_bg = "#e1e1e1"
        self.clean_hover_bg = "#e5f1fb"
        self.clean_click_bg = "#cce4f7"
        self.clean_border_color = "#adadad"
        self.clean_hover_border = "#0078d7"
        self.clean_click_border = "#005499"

        self.retro_label_bg = "#f0f0f0"

        # Clean theme styles
        self.style.configure("cleanFrameButtonSurface.TFrame", background=self.clean_label_bg, relief="solid", borderwidth=0)
        self.style.configure("cleanFrameButtonHoverSurface.TFrame", background=self.clean_hover_bg, relief="solid", borderwidth=0)
        self.style.configure("cleanFrameButtonClickSurface.TFrame", background=self.clean_click_bg, relief="solid", borderwidth=0)
        self.style.configure("cleanFrameButton.TLabel", background=self.clean_label_bg, font=self.font_pairs['font8'])
        self.style.configure("cleanFrameButtonHover.TLabel", background=self.clean_hover_bg, font=self.font_pairs['font8'])
        self.style.configure("cleanFrameButtonClick.TLabel", background=self.clean_click_bg, font=self.font_pairs['font8'])
        self.style.configure("cleanFrameButtonText.TLabel", background=self.clean_label_bg, font=self.font_pairs['font6'])
        self.style.configure("cleanFrameButtonHoverText.TLabel", background=self.clean_hover_bg, font=self.font_pairs['font6'])
        self.style.configure("cleanFrameButtonClickText.TLabel", background=self.clean_click_bg, font=self.font_pairs['font6'])

        # Retro theme styles
        self.style.configure("retroFrameButtonSurface.TFrame", background=self.retro_label_bg, relief="flat", borderwidth=0)
        self.style.configure("retroFrameButtonHoverSurface.TFrame", background=self.retro_label_bg, relief="flat", borderwidth=0)
        self.style.configure("retroFrameButtonClickSurface.TFrame", background=self.retro_label_bg, relief="flat", borderwidth=0)
        self.style.configure("retroFrameButton.TLabel", background=self.retro_label_bg, font=self.font_pairs['font8'])
        self.style.configure("retroFrameButtonHover.TLabel", background=self.retro_label_bg, font=self.font_pairs['font8'])
        self.style.configure("retroFrameButtonClick.TLabel", background=self.retro_label_bg, font=self.font_pairs['font8'])
        self.style.configure("retroFrameButtonText.TLabel", background=self.retro_label_bg, font=self.font_pairs['font6'])
        self.style.configure("retroFrameButtonHoverText.TLabel", background=self.retro_label_bg, font=self.font_pairs['font6'])
        self.style.configure("retroFrameButtonClickText.TLabel", background=self.retro_label_bg, font=self.font_pairs['font6'])

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
                self.outer_frame.config(bg='', bd=2, relief="raised")  # No background for correct relief shadow
                self.inner_frame.config(bg=self.retro_label_bg)
            elif state == "Click":
                self.outer_frame.config(bg='', bd=2, relief="sunken")  # No background for correct relief shadow
                self.inner_frame.config(bg=self.retro_label_bg)
            else:
                self.outer_frame.config(bg='', bd=2, relief="raised")  # No background for correct relief shadow
                self.inner_frame.config(bg=self.retro_label_bg)

        # Set the background color of the surface to match the inner frame
        self.surface.config(bg=self.inner_frame.cget("bg"))

        # Apply styles to labels
        for widget in self.surface.winfo_children():
            widget_name = str(widget)
            if "_font12" in widget_name:
                widget.configure(font=self.font_pairs['font12'])
            elif "_font10" in widget_name:
                widget.configure(font=self.font_pairs['font10'])
            elif "_font8" in widget_name:
                widget.configure(font=self.font_pairs['font8'])
            elif "_font6" in widget_name:
                widget.configure(font=self.font_pairs['font6'])
            
            # Apply styles only to supported widgets
            if isinstance(widget, ttk.Label) or isinstance(widget, ttk.Button) or isinstance(widget, ttk.Checkbutton) or isinstance(widget, ttk.Radiobutton) or isinstance(widget, ttk.Combobox):
                widget.configure(style=label_style if isinstance(widget, ttk.Label) else text_style)

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
        self.root.geometry("380x420")

        self.style = ttk.Style()
        self.theme_var = tk.StringVar(value="Clean")
        self.style.theme_use('xpnative')

        main_frame = ttk.Frame(root)
        main_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.toolbox_frame = ttk.Frame(main_frame)
        self.toolbox_frame.grid_columnconfigure(0, weight=1)
        self.toolbox_frame.grid_columnconfigure(1, weight=1)
        self.toolbox_frame.grid_columnconfigure(2, weight=1)
        self.toolbox_frame.grid_rowconfigure(0, weight=1)
        self.toolbox_frame.grid_rowconfigure(1, weight=1)
        self.toolbox_frame.grid_rowconfigure(2, weight=1)
        self.toolbox_frame.pack(expand=False, fill=tk.BOTH)

        self.mouse_tracker_button = FancyButton(self.toolbox_frame, self.create_mouse_tracker_surface, self.theme_var, self.toggle_mouse_tracking)
        self.mouse_tracker_button.outer_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.prompt_button = FancyButton(self.toolbox_frame, self.create_prompt_surface, self.theme_var, self.open_prompt_dropdown)
        self.prompt_button.outer_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        self.taskmanager_button = FancyButton(self.toolbox_frame, self.create_taskmanager_surface, self.theme_var, self.task_manager_click)
        self.taskmanager_button.outer_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")

        self.spinbox_button = FancyButton(self.toolbox_frame, self.create_spinbox_surface, self.theme_var, self.sample_function_spinbox)
        self.spinbox_button.outer_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        self.radiobutton_button = FancyButton(self.toolbox_frame, self.create_radiobutton_surface, self.theme_var, self.sample_function_radiobutton)
        self.radiobutton_button.outer_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        self.scale_button = FancyButton(self.toolbox_frame, self.create_scale_surface, self.theme_var, self.sample_function_scale)
        self.scale_button.outer_frame.grid(row=1, column=2, padx=5, pady=5, sticky="nsew")

        self.listbox_button = FancyButton(self.toolbox_frame, self.create_listbox_surface, self.theme_var, self.sample_function_listbox)
        self.listbox_button.outer_frame.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")

        self.canvas_button = FancyButton(self.toolbox_frame, self.create_canvas_surface, self.theme_var, self.sample_function_canvas)
        self.canvas_button.outer_frame.grid(row=2, column=1, padx=5, pady=5, sticky="nsew")

        self.progressbar_button = FancyButton(self.toolbox_frame, self.create_progressbar_surface, self.theme_var, self.sample_function_progressbar)
        self.progressbar_button.outer_frame.grid(row=2, column=2, padx=5, pady=5, sticky="nsew")

        self.toggle_theme_button = ttk.Button(main_frame, text="Toggle Theme", command=self.toggle_theme)
        self.toggle_theme_button.pack(padx=5, pady=10)

    def create_taskmanager_surface(self, parent):
        self.taskmanager_fb_title_font8 = ttk.Label(parent, text="Task Manager", anchor="center", style="cleanFrameButton.TLabel", width=12)
        self.taskmanager_fb_title_font8.pack(fill=tk.X, padx=5, pady=(2, 0))
        self.taskmanager_fb_sep = ttk.Separator(parent, orient="horizontal")
        self.taskmanager_fb_sep.pack(fill=tk.X, padx=5, pady=0)
        self.taskmanager_fb_cpu_font6 = ttk.Label(parent, text="CPU:  0%", style="cleanFrameButtonText.TLabel", anchor="w")
        self.taskmanager_fb_cpu_font6.pack(fill=tk.X, padx=10, pady=(0, 0))
        self.taskmanager_fb_ram_font6 = ttk.Label(parent, text="RAM:  0%", style="cleanFrameButtonText.TLabel", anchor="w")
        self.taskmanager_fb_ram_font6.pack(fill=tk.X, padx=10, pady=0)
        self.taskmanager_fb_disk_font6 = ttk.Label(parent, text="DISK: 0%", style="cleanFrameButtonText.TLabel", anchor="w")
        self.taskmanager_fb_disk_font6.pack(fill=tk.X, padx=10, pady=0)
        self.taskmanager_fb_up_font6 = ttk.Label(parent, text="UP:   0 MB", style="cleanFrameButtonText.TLabel", anchor="w")
        self.taskmanager_fb_up_font6.pack(fill=tk.X, padx=10, pady=0)
        self.taskmanager_fb_down_font6 = ttk.Label(parent, text="DOWN: 0 MB", style="cleanFrameButtonText.TLabel", anchor="w")
        self.taskmanager_fb_down_font6.pack(fill=tk.X, padx=10, pady=(0, 2))

    def create_prompt_surface(self, parent):
        self.prompt_fb_title_font12 = ttk.Label(parent, text="Prompt Chooser", anchor="center", style="cleanFrameButton.TLabel")
        self.prompt_fb_title_font12.pack(fill=tk.X, padx=5, pady=(2, 0))
        self.prompt_fb_sep = ttk.Separator(parent, orient="horizontal")
        self.prompt_fb_sep.pack(fill=tk.X, padx=5, pady=0)
        self.prompt_fb_dropdown = ttk.Combobox(parent, textvariable=tk.StringVar(value="Terminal"), values=["Terminal", "PowerShell", "cmd"], state="readonly", width=10)
        self.prompt_fb_dropdown.pack(fill=tk.X, padx=5, pady=5)
        self.prompt_fb_admin_check = ttk.Checkbutton(parent, text="Admin", variable=tk.IntVar())
        self.prompt_fb_admin_check.pack(fill=tk.X, padx=5, pady=5)
        self.prompt_fb_label_font10 = ttk.Label(parent, text="Prompt", anchor="center", style="cleanFrameButton.TLabel")
        self.prompt_fb_label_font10.pack(fill=tk.BOTH, padx=5, pady=5, ipady=5)

    def create_mouse_tracker_surface(self, parent):
        self.mouse_tracker_fb_title_font12 = ttk.Label(parent, text="Mouse Tracker", style="cleanFrameButton.TLabel", anchor="center", width=12)
        self.mouse_tracker_fb_title_font12.pack(fill=tk.X, padx=5, pady=(2, 0))
        self.mouse_tracker_fb_sep = ttk.Separator(parent, orient="horizontal")
        self.mouse_tracker_fb_sep.pack(fill=tk.X, padx=5, pady=0)
        self.mouse_tracker_fb_pixel_font10 = ttk.Label(parent, text=f"Pixel:          (0, 0)\nWindows:  (0, 0)", anchor="w")
        self.mouse_tracker_fb_pixel_font10.pack(fill=tk.X, padx=10, pady=2)
        self.mouse_tracker_fb_start_font10 = ttk.Label(parent, text="Start Tracking", anchor="center", style="cleanFrameButton.TLabel")
        self.mouse_tracker_fb_start_font10.pack(fill=tk.BOTH, padx=5, pady=5, ipady=5)

    def create_spinbox_surface(self, parent):
        self.spinbox_fb_title_font12 = ttk.Label(parent, text="Spinbox", anchor="center", style="cleanFrameButton.TLabel")
        self.spinbox_fb_title_font12.pack(fill=tk.X, padx=5, pady=(2, 0))
        self.spinbox_fb_spinbox = ttk.Spinbox(parent, from_=0, to=10, width=6)
        self.spinbox_fb_spinbox.pack(fill=tk.X, padx=5, pady=5)
        self.spinbox_fb_font10 = ttk.Label(parent, text="Font Size 10", anchor="center", style="cleanFrameButton.TLabel")
        self.spinbox_fb_font10.pack(fill=tk.X, padx=5, pady=(2, 0))

    def create_radiobutton_surface(self, parent):
        self.radiobutton_fb_title_font12 = ttk.Label(parent, text="Radiobutton", anchor="center", style="cleanFrameButton.TLabel")
        self.radiobutton_fb_title_font12.pack(fill=tk.X, padx=5, pady=(2, 0))
        self.radio_var = tk.StringVar()
        self.radiobutton_fb_option1_font10 = ttk.Radiobutton(parent, text="Option 1", variable=self.radio_var, value="Option 1")
        self.radiobutton_fb_option1_font10.pack(fill=tk.X, padx=5, pady=5)
        self.radiobutton_fb_option2_font10 = ttk.Radiobutton(parent, text="Option 2", variable=self.radio_var, value="Option 2")
        self.radiobutton_fb_option2_font10.pack(fill=tk.X, padx=5, pady=5)
        self.radiobutton_fb_font10 = ttk.Label(parent, text="Font Size 10", anchor="center", style="cleanFrameButton.TLabel")
        self.radiobutton_fb_font10.pack(fill=tk.X, padx=5, pady=(2, 0))

    def create_scale_surface(self, parent):
        self.scale_fb_title_font12 = ttk.Label(parent, text="Scale", anchor="center", style="cleanFrameButton.TLabel")
        self.scale_fb_title_font12.pack(fill=tk.X, padx=5, pady=(2, 0))
        self.scale_fb_scale = ttk.Scale(parent, from_=0, to=100)
        self.scale_fb_scale.pack(fill=tk.X, padx=5, pady=5)
        self.scale_fb_font10 = ttk.Label(parent, text="Font Size 10", anchor="center", style="cleanFrameButton.TLabel")
        self.scale_fb_font10.pack(fill=tk.X, padx=5, pady=(2, 0))

    def create_listbox_surface(self, parent):
        self.listbox_fb_title_font12 = ttk.Label(parent, text="Listbox", anchor="center", style="cleanFrameButton.TLabel")
        self.listbox_fb_title_font12.pack(fill=tk.X, padx=5, pady=(2, 0))
        self.listbox_fb_listbox = tk.Listbox(parent, width=10, height=5)
        self.listbox_fb_listbox.pack(fill=tk.X, padx=5, pady=5)
        for i in range(1, 11):
            self.listbox_fb_listbox.insert(tk.END, f"Item {i}")
        self.listbox_fb_font10 = ttk.Label(parent, text="Font Size 10", anchor="center", style="cleanFrameButton.TLabel")
        self.listbox_fb_font10.pack(fill=tk.X, padx=5, pady=(2, 0))

    def create_canvas_surface(self, parent):
        self.canvas_fb_title_font12 = ttk.Label(parent, text="Canvas", anchor="center", style="cleanFrameButton.TLabel")
        self.canvas_fb_title_font12.pack(fill=tk.X, padx=5, pady=(2, 0))
        self.canvas_fb_canvas = tk.Canvas(parent, width=100, height=50, bg="white")
        self.canvas_fb_canvas.pack(fill=tk.X, padx=5, pady=5)
        self.canvas_fb_canvas.create_oval(10, 10, 90, 40, fill="blue")
        self.canvas_fb_font10 = ttk.Label(parent, text="Font Size 10", anchor="center", style="cleanFrameButton.TLabel")
        self.canvas_fb_font10.pack(fill=tk.X, padx=5, pady=(2, 0))

    def create_progressbar_surface(self, parent):
        self.progressbar_fb_title_font12 = ttk.Label(parent, text="Progressbar", anchor="center", style="cleanFrameButton.TLabel")
        self.progressbar_fb_title_font12.pack(fill=tk.X, padx=5, pady=(2, 0))
        self.progressbar_fb_progressbar = ttk.Progressbar(parent, value=50)
        self.progressbar_fb_progressbar.pack(fill=tk.X, padx=5, pady=5)
        self.progressbar_fb_font10 = ttk.Label(parent, text="Font Size 10", anchor="center", style="cleanFrameButton.TLabel")
        self.progressbar_fb_font10.pack(fill=tk.X, padx=5, pady=(2, 0))

    def toggle_theme(self):
        if self.theme_var.get() == "Clean":
            self.theme_var.set("Retro")
            self.style.theme_use('winnative')
        else:
            self.theme_var.set("Clean")
            self.style.theme_use('xpnative')
        self.update_styles()

    def update_styles(self):
        self.taskmanager_button.update_style("")
        self.prompt_button.update_style("")
        self.mouse_tracker_button.update_style("")
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
        selected_prompt = self.prompt_fb_dropdown.get()
        print(f"Opening prompt dropdown: {selected_prompt}")

    def toggle_mouse_tracking(self):
        print("Toggling mouse tracking")

    def sample_function_spinbox(self):
        value = self.spinbox_fb_spinbox.get()
        print(f"Spinbox value: {value}")

    def sample_function_radiobutton(self):
        selected_option = self.radio_var.get()
        print(f"Selected radiobutton: {selected_option}")

    def sample_function_scale(self):
        value = self.scale_fb_scale.get()
        print(f"Scale value: {value}")

    def sample_function_listbox(self):
        selected_items = [self.listbox_fb_listbox.get(i) for i in self.listbox_fb_listbox.curselection()]
        print(f"Selected listbox items: {selected_items}")

    def sample_function_canvas(self):
        print("Canvas clicked")

    def sample_function_progressbar(self):
        value = self.progressbar_fb_progressbar['value']
        print(f"Progressbar value: {value}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FancyButtonTestApp(root)
    root.mainloop()
