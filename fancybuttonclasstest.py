# HIDEOUS but it's getting closer



import tkinter as tk
from tkinter import ttk
import subprocess
import re




LIGHT_COLORS = {
    'clean': {
        'label_bg': "#e1e1e1",
        'hover_bg': "#c7e0f4",
        'click_bg': "#a9d1f5",
        'border_color': "#adadad",
        'hover_border': "#0078d7",
        'click_border': "#005499",
        'text_color': "#000000"
    },
        'retro': {
        'label_bg': "#f0f0f0",
        'hover_bg': "#f0f0f0",
        'click_bg': "#f0f0f0",
        'border_color': "#c0c0c0",
        'hover_border': "#a0a0a0",
        'click_border': "#a0a0a0",
        'text_color': "#000000"
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
        'text_color': "#ffffff"
    },
    'retro': {
        'label_bg': "#404040",
        'hover_bg': "#404040",
        'click_bg': "#404040",
        'border_color': "#808080",
        'hover_border': "#808080",
        'click_border': "#808080",
        'text_color': "#ffffff"
    }
}




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
            # All widgets get enter and leave events
            child.bind("<Enter>", self.on_enter_child)
            child.bind("<Leave>", self.on_leave_child)
            
            # Most widgets trigger the FancyButton's click and release events
            if not isinstance(child, (ttk.Entry, ttk.Spinbox, ttk.Combobox, ttk.Scale, ttk.Checkbutton)): # OMIT these from triggering the fancybutton-click
                
                child.bind("<Button-1>", self.on_click_child)
                child.bind("<ButtonRelease-1>", self.on_release_child)
            
            # Special bindings
            elif isinstance(child, (ttk.Radiobutton)): # INCLUDE in triggering fancybutton-click | more options: ttk.Checkbutton, Entry, Spinbox, Combobox, and Scale
                child.bind("<Button-1>", self.on_interactive_widget_click)
                child.bind("<ButtonRelease-1>", self.on_interactive_widget_release)
            
            # Recursively bind children of this widget (handles nested frames)
            if hasattr(child, 'winfo_children'):
                self.bind_children(child)



    def on_interactive_widget_click(self, event):
        self.update_style("Click")
        event.widget.event_generate("<<ThemeChanged>>")

    def on_interactive_widget_release(self, event):
        if self.is_mouse_within_bounds(event.x_root, event.y_root):
            self.collect_widget_info()
        self.update_style("Hover" if self.is_hovered else "")
        event.widget.event_generate("<<ThemeChanged>>")

    def on_enter(self, event):
        self.update_style("Hover")
        self.is_hovered = True

    def on_leave(self, event):
        self.is_hovered = False
        self.update_style("")

    def on_enter_child(self, event):
        self.is_hovered = True
        self.update_style("Hover")

    def on_leave_child(self, event):
        if not self.is_mouse_within_bounds(event.x_root, event.y_root):
            self.is_hovered = False
            self.update_style("")

    def on_click(self, event):
        self.update_style("Click")
        self.collect_widget_info()

    def on_release(self, event):
        if self.is_mouse_within_bounds(event.x_root, event.y_root):
            self.command()
            self.collect_widget_info()
        self.update_style("Hover" if self.is_hovered else "")

    def on_click_child(self, event):
        self.update_style("Click")
        self.collect_widget_info() 

    def on_release_child(self, event):
        if self.is_mouse_within_bounds(event.x_root, event.y_root):
            if isinstance(event.widget, tk.Canvas):
                self.on_canvas_click(event, event.widget)
            self.command()
        self.update_style("Hover" if self.is_hovered else "")

    def update_style(self, state):
        theme = self.theme_var.get().lower()
        mode = "dark" if self.dark_mode_var.get() else "light"
        colors = DARK_COLORS[theme] if mode == "dark" else LIGHT_COLORS[theme]

        bg_color = colors['label_bg']
        fg_color = colors['text_color']

        if theme == "clean":
            if state == "Hover":
                self.outer_frame.config(bg=colors['hover_border'], bd=0)
                self.inner_frame.config(bg=colors['hover_bg'])
            elif state == "Click":
                self.outer_frame.config(bg=colors['click_border'], bd=0)
                self.inner_frame.config(bg=colors['click_bg'])
            else:
                self.outer_frame.config(bg=colors['border_color'], bd=0)
                self.inner_frame.config(bg=colors['label_bg'])
        elif theme == "retro":
            self.outer_frame.config(bg=colors['border_color'], bd=2, relief="raised")
            self.inner_frame.config(bg=colors['label_bg'], bd=0)
            if state == "Click":
                self.outer_frame.config(relief="sunken")
            else:
                self.outer_frame.config(relief="raised")

        self.surface.config(bg=self.inner_frame.cget("bg"))
        self.style_descendants(self.surface, bg_color, fg_color, state)

    def style_descendants(self, widget, bg_color, fg_color, state):
        for child in widget.winfo_children():
            if isinstance(child, ttk.Widget):
                self.style_ttk_widget(child, bg_color, fg_color, state)
            elif isinstance(child, tk.Widget):
                self.style_tk_widget(child, bg_color, fg_color, state)

            if isinstance(child, ttk.Frame):
                child.configure(style='')
                self.style.configure('TFrame', background=bg_color)

            if hasattr(child, 'winfo_children'):
                self.style_descendants(child, bg_color, fg_color, state)

    def style_tk_widget(self, widget, bg_color, fg_color, state):
        widget_class = widget.winfo_class()
        if widget_class in ['Label', 'Button', 'Radiobutton', 'Checkbutton']:
            font_size = self.get_font_size(widget)
            widget.configure(bg=bg_color, fg=fg_color, font=("TkDefaultFont", font_size))
        elif widget_class == 'Entry':
            widget.configure(bg=bg_color, fg=fg_color, insertbackground=fg_color)
        elif widget_class in ['Frame', 'Canvas']:
            widget.configure(bg=bg_color)
        elif widget_class == 'Listbox':
            listbox_bg = "#ffffff" if self.theme_var.get().lower() in ["clean", "retro"] and not self.dark_mode_var.get() else bg_color
            font_size = self.get_font_size(widget)
            widget.configure(bg=listbox_bg, fg=fg_color, font=("TkDefaultFont", font_size))

    def style_ttk_widget(self, widget, bg_color, fg_color, state):
        widget_class = widget.winfo_class()
        font_size = self.get_font_size(widget)
        theme = self.theme_var.get().lower()
        mode = "dark" if self.dark_mode_var.get() else "light"
        
        if widget_class == 'TLabel':
            if theme == "clean":
                if state == "Hover":
                    bg_color = LIGHT_COLORS['clean']['hover_bg'] if mode == "light" else DARK_COLORS['clean']['hover_bg']
                elif state == "Click":
                    bg_color = LIGHT_COLORS['clean']['click_bg'] if mode == "light" else DARK_COLORS['clean']['click_bg']
            
            widget.configure(style='', background=bg_color, foreground=fg_color, font=("TkDefaultFont", font_size))
        elif widget_class in ['TEntry', 'TSpinbox', 'TCombobox']:
            style_name = f'Custom.{widget_class}'
            if theme == "retro" and mode == "light":
                self.style.configure(style_name, fieldbackground='#ffffff', foreground=fg_color, font=("TkDefaultFont", font_size))
                self.style.map(style_name, fieldbackground=[('readonly', '#ffffff')])
            else:
                self.style.configure(style_name, fieldbackground=bg_color, foreground=fg_color, font=("TkDefaultFont", font_size))
                self.style.map(style_name, fieldbackground=[('readonly', bg_color)])
            widget.configure(style=style_name)
        elif widget_class == 'TScale':
            self.style.configure(widget_class, troughcolor=bg_color)
        elif widget_class == 'TProgressbar':
            if theme == "retro":
                self.style.configure(widget_class, background='blue', troughcolor='white' if mode == "light" else 'gray')
            else:
                self.style.configure(widget_class, background=bg_color, troughcolor=bg_color)
        elif widget_class in ['TFrame', 'TLabelframe']:
            widget.configure(style='')
            self.style.configure(widget_class, background=bg_color)
        elif widget_class in ['TRadiobutton', 'TCheckbutton']:
            style_name = f'Custom.{widget_class}'
            if theme == "clean":
                if state == "Hover":
                    bg_color = LIGHT_COLORS['clean']['hover_bg'] if mode == "light" else DARK_COLORS['clean']['hover_bg']
                elif state == "Click":
                    bg_color = LIGHT_COLORS['clean']['click_bg'] if mode == "light" else DARK_COLORS['clean']['click_bg']
            self.style.configure(style_name, background=bg_color, foreground=fg_color)
            widget.configure(style=style_name)


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
        
        # Recursively collect info for child widgets (e.g., in frames)
        if hasattr(widget, 'winfo_children'):
            for child in widget.winfo_children():
                self._collect_widget_info_recursive(child)

    def on_canvas_click(self, event, canvas):
        x, y = event.x, event.y
        self.widget_info[canvas.winfo_name()] = f"Clicked at ({x}, {y})"

    def recreate(self):
        grid_info = self.outer_frame.grid_info()
        self.outer_frame.destroy()
        self.__init__(self.parent, self.create_surface, self.theme_var, self.dark_mode_var, self.command)
        self.outer_frame.grid(**grid_info)
        
class FancyButtonTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FancyButton Test Application")
        self.root.geometry("420x600")

        self.radio_triggers_command = True

        self.style = ttk.Style()
        self.theme_var = tk.StringVar(value="Clean")
        self.dark_mode_var = tk.BooleanVar(value=False)
        self.style.theme_use('xpnative')

        self.main_frame = ttk.Frame(root, style='Main.TFrame')
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        self.toolbox_frame = ttk.Frame(self.main_frame, style='Toolbox.TFrame')
        self.toolbox_frame.pack(expand=False, fill=tk.BOTH)


        self.buttons = []
        button_configs = [
            ("taskmanager", self.create_taskmanager_surface, self.task_manager_click),
            ("prompt", self.create_prompt_surface, self.prompt_click),
            ("mouse_tracker", self.create_mouse_tracker_surface, self.mouse_tracker_click),
            ("spinbox", self.create_spinbox_surface, self.spinbox_click),
            ("radiobutton", self.create_radiobutton_surface, self.radiobutton_click),
            ("scale", self.create_scale_surface, self.scale_click),
            ("listbox", self.create_listbox_surface, self.listbox_click),
            ("canvas", self.create_canvas_surface, self.on_canvas_click),
            ("progressbar", self.create_progressbar_surface, self.progressbar_click)
        ]

        for i, (name, create_func, click_func) in enumerate(button_configs):
            button = FancyButton(self.toolbox_frame, create_func, self.theme_var, self.dark_mode_var, click_func)
            button.outer_frame.grid(row=i // 3, column=i % 3, padx=5, pady=5, sticky="nsew")
            self.buttons.append(button)

        for i in range(3):
            self.toolbox_frame.columnconfigure(i, weight=1)
        for i in range(3):
            self.toolbox_frame.rowconfigure(i, weight=1)

        control_frame = ttk.Frame(self.main_frame, style='Control.TFrame')
        control_frame.pack(pady=10)

        self.toggle_theme_button = ttk.Button(control_frame, text="Toggle Theme", command=self.toggle_theme)
        self.toggle_theme_button.pack(side=tk.LEFT, padx=5)

        self.dark_mode_check = ttk.Checkbutton(control_frame, text="Dark Mode", variable=self.dark_mode_var, command=self.toggle_dark_mode)
        self.dark_mode_check.pack(side=tk.LEFT, padx=5)

        self.update_app_style()


    def create_taskmanager_surface(self, surface):
        ttk.Label(surface, text="Task Manager", anchor="center", width=12, name="tm_title_font8").pack(fill=tk.X, padx=5, pady=(2, 0))
        ttk.Separator(surface, orient="horizontal").pack(fill=tk.X, padx=5, pady=0)
        ttk.Label(surface, text="CPU:  0%", anchor="w", name="tm_cpu_font6").pack(fill=tk.X, padx=10, pady=(0, 0))
        ttk.Label(surface, text="RAM:  0%", anchor="w", name="tm_ram_font6").pack(fill=tk.X, padx=10, pady=0)
        ttk.Label(surface, text="DISK: 0%", anchor="w", name="tm_disk_font6").pack(fill=tk.X, padx=10, pady=0)
        ttk.Label(surface, text="UP:   0 MB", anchor="w", name="tm_up_font6").pack(fill=tk.X, padx=10, pady=0)
        ttk.Label(surface, text="DOWN: 0 MB", anchor="w", name="tm_down_font6").pack(fill=tk.X, padx=10, pady=(0, 2))
        return surface.winfo_children()


    def create_prompt_surface(self, surface):
        ttk.Label(surface, text="Prompt Chooser", anchor="center", name="pc_title_font12").pack(fill=tk.X, padx=5, pady=(2, 0))
        ttk.Separator(surface, orient="horizontal").pack(fill=tk.X, padx=5, pady=0)
        combobox = ttk.Combobox(surface, values=["Terminal", "PowerShell", "cmd"], state="readonly", width=10, name="pc_combo_font10")
        combobox.set("Terminal")
        combobox.pack(fill=tk.X, padx=5, pady=5)
        
        bottom_frame = ttk.Frame(surface, name="pc_bottom_frame")
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.admin_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(bottom_frame, text="Admin", variable=self.admin_var, name="pc_admin_check_font10").pack(side=tk.LEFT)
        ttk.Label(bottom_frame, text="Prompt", anchor="center", name="pc_prompt_font12").pack(side=tk.LEFT, padx=(5, 0))
        
        return surface.winfo_children()

    def create_mouse_tracker_surface(self, surface):
        ttk.Label(surface, text="Mouse Tracker", anchor="center", width=12, name="mt_title_font12").pack(fill=tk.X, padx=5, pady=(2, 0))
        ttk.Separator(surface, orient="horizontal").pack(fill=tk.X, padx=5, pady=0)
        ttk.Label(surface, text="Pixel:          (0, 0)\nWindows:  (0, 0)", anchor="w", name="mt_coordinates_font8").pack(fill=tk.X, padx=10, pady=2)
        ttk.Label(surface, text="Start Tracking", anchor="center", name="mt_start_font10").pack(fill=tk.BOTH, padx=5, pady=5, ipady=5)
        return surface.winfo_children()

    def create_spinbox_surface(self, surface):
        ttk.Label(surface, text="Spinbox", anchor="center", name="sb_title_font12").pack(fill=tk.X, padx=5, pady=(2, 0))
        spinbox = ttk.Spinbox(surface, from_=0, to=10, width=6, name="sb_value_font10")
        spinbox.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(surface, text="Font Size 10", anchor="center", name="sb_label_font10").pack(fill=tk.X, padx=5, pady=(2, 0))
        return surface.winfo_children()

    def create_radiobutton_surface(self, surface):
        ttk.Label(surface, text="Radiobutton", anchor="center", name="rb_title_font12").pack(fill=tk.X, padx=5, pady=(2, 0))
        self.radio_var = tk.StringVar(value="")  # No default selection
        ttk.Radiobutton(surface, text="Option 1", variable=self.radio_var, value="Option 1", name="rb_option1_font8", 
                        command=self.on_radio_click if self.radio_triggers_command else None).pack(fill=tk.X, padx=5, pady=5)
        ttk.Radiobutton(surface, text="Option 2", variable=self.radio_var, value="Option 2", name="rb_option2_font12", 
                        command=self.on_radio_click if self.radio_triggers_command else None).pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(surface, text="Font Size 6", anchor="center", name="rb_label_font6").pack(fill=tk.X, padx=5, pady=(2, 0))
        return surface.winfo_children()

    def create_scale_surface(self, surface):
        ttk.Label(surface, text="Scale", anchor="center", name="sc_title_font12").pack(fill=tk.X, padx=5, pady=(2, 0))
        scale = ttk.Scale(surface, from_=0, to=100, name="sc_value_font10")
        scale.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(surface, text="Font Size 10", anchor="center", name="sc_label_font10").pack(fill=tk.X, padx=5, pady=(2, 0))
        return surface.winfo_children()

    def create_listbox_surface(self, surface):
        ttk.Label(surface, text="Listbox", anchor="center", name="lb_title_font12").pack(fill=tk.X, padx=5, pady=(2, 0))
        frame = ttk.Frame(surface)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.listbox = tk.Listbox(frame, width=10, height=5, name="lb_items_font8")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        for i in range(1, 21):
            self.listbox.insert(tk.END, f"Item {i}")
        ttk.Label(surface, text="Font Size 8", anchor="center", name="lb_label_font8").pack(fill=tk.X, padx=5, pady=(2, 0))
        return surface.winfo_children()

    def create_canvas_surface(self, surface):
        ttk.Label(surface, text="Canvas", anchor="center", name="cv_title_font12").pack(fill=tk.X, padx=5, pady=(2, 0))
        canvas = tk.Canvas(surface, width=100, height=50, bg="white", name="cv_main")
        canvas.pack(fill=tk.X, padx=5, pady=5)
        canvas.create_oval(10, 10, 90, 40, fill="blue")
        ttk.Label(surface, text="Font Size 12", anchor="center", name="cv_label_font12").pack(fill=tk.X, padx=5, pady=(2, 0))
        return surface.winfo_children()

    def create_progressbar_surface(self, surface):
        ttk.Label(surface, text="Progressbar", anchor="center", name="pb_title_font12").pack(fill=tk.X, padx=5, pady=(2, 0))
        progress = ttk.Progressbar(surface, value=50, name="pb_main")
        progress.pack(fill=tk.X, padx=5, pady=5)
        
        entry_frame = ttk.Frame(surface, name="pb_entry_frame")
        entry_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.pb_entry = ttk.Entry(entry_frame, name="pb_entry_font10")
        self.pb_entry.insert(0, "Neat!")
        self.pb_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(surface, text="Font Size 10", anchor="center", name="pb_label_font10").pack(fill=tk.X, padx=5, pady=(2, 0))
        return surface.winfo_children()


    def update_app_style(self):
        theme = self.theme_var.get().lower()
        mode = "dark" if self.dark_mode_var.get() else "light"
        colors = DARK_COLORS[theme] if mode == "dark" else LIGHT_COLORS[theme]

        bg_color = colors['label_bg']
        fg_color = colors['text_color']

        self.style.configure('Main.TFrame', background=bg_color)
        self.style.configure('Toolbox.TFrame', background=bg_color)
        self.style.configure('Control.TFrame', background=bg_color)
        self.style.configure('TButton', background=bg_color, foreground=fg_color)
        self.style.configure('TCheckbutton', background=bg_color, foreground=fg_color)

        # Update toggle theme button style
        if mode == "dark":
            self.toggle_theme_button.configure(style='')
            self.style.configure('TButton', background='#333333', foreground='white')
        else:
            self.toggle_theme_button.configure(style='')
            self.style.configure('TButton', background='#f0f0f0', foreground='black')

        self.root.configure(bg=bg_color)

    def toggle_theme(self):
        if self.theme_var.get() == "Clean":
            self.theme_var.set("Retro")
            self.style.theme_use('winnative')
        else:
            self.theme_var.set("Clean")
            self.style.theme_use('xpnative')
        self.update_app_style()
        self.recreate_buttons()


    def toggle_dark_mode(self):
        self.update_app_style()
        self.recreate_buttons()

    def recreate_buttons(self):
        for button in self.buttons:
            button.recreate()




    def task_manager_click(self):
        print("Task Manager Clicked")
        subprocess.Popen(["powershell", "-Command", "Start-Process taskmgr -Verb runAs"])
        button = next(b for b in self.buttons if b.command == self.task_manager_click)
        for widget, value in button.widget_info.items():
            print(f"  {widget}: {value}")

    def prompt_click(self):
        print("Prompt Chooser Clicked")
        button = next(b for b in self.buttons if b.command == self.prompt_click)
        for widget, value in button.widget_info.items():
            print(f"  {widget}: {value}")

    def mouse_tracker_click(self):
        print("Mouse Tracker Clicked")
        button = next(b for b in self.buttons if b.command == self.mouse_tracker_click)
        for widget, value in button.widget_info.items():
            print(f"  {widget}: {value}")

    def spinbox_click(self):
        print("Spinbox Button Clicked")
        button = next(b for b in self.buttons if b.command == self.spinbox_click)
        for widget, value in button.widget_info.items():
            print(f"  {widget}: {value}")

    def on_radio_click(self):
        if self.radio_triggers_command:
            self.radiobutton_click()

    def radiobutton_click(self):
        print("Radiobutton Button Clicked")
        button = next(b for b in self.buttons if b.command == self.radiobutton_click)
        selected_option = self.radio_var.get()
        print(f"  Selected option: {selected_option}")
        for widget, value in button.widget_info.items():
            print(f"  {widget}: {value}")

    def scale_click(self):
        print("Scale Button Clicked")
        button = next(b for b in self.buttons if b.command == self.scale_click)
        for widget, value in button.widget_info.items():
            print(f"  {widget}: {value}")

    def listbox_click(self):
        print("Listbox Button Clicked")
        button = next(b for b in self.buttons if b.command == self.listbox_click)
        listbox_info = button.widget_info.get("lb_items_font8", "Listbox not found")
        print(f"  Selected item: {listbox_info}")
        
        # For debugging, let's print the actual selection directly from the listbox
        selection = self.listbox.curselection()
        if selection:
            print(f"  Direct listbox selection: {self.listbox.get(selection[0])}")
        else:
            print("  Direct listbox selection: No selection")

        for widget, value in button.widget_info.items():
            if widget != "lb_items_font8":
                print(f"  {widget}: {value}")
                
    def on_canvas_click(self):
        print("Canvas Button Clicked")
        button = next(b for b in self.buttons if b.command == self.on_canvas_click)
        for widget, value in button.widget_info.items():
            if widget == "cv_main" and value.startswith("Clicked at"):
                print(f"  Canvas {value}")
            else:
                print(f"  {widget}: {value}")

    def progressbar_click(self):
        print("Progressbar Button Clicked")
        button = next(b for b in self.buttons if b.command == self.progressbar_click)
        for widget, value in button.widget_info.items():
            print(f"  {widget}: {value}")
        print(f"  Entry content: {self.pb_entry.get()}")



if __name__ == "__main__":
    root = tk.Tk()
    app = FancyButtonTestApp(root)
    root.mainloop()




"""
    #Find a widget by its name.
    def find_widget_by_name(self, name):
        return self.widget_dict.get(name)

    # Update the text of a label identified by its name
    def update_label_text(self, name, new_text):
        widget = self.find_widget_by_name(name)
        if widget and isinstance(widget, ttk.Label):
            widget.config(text=new_text)
        else:
            print(f"Widget '{name}' not found or is not a Label.")



    def update_task_manager_info(self):
        self.update_label_text("cpu_font6", f"CPU:  {self.get_cpu_usage()}%")
        self.update_label_text("ram_font6", f"RAM:  {self.get_ram_usage()}%")
        self.update_label_text("disk_font6", f"DISK: {self.get_disk_usage()}%")
        self.update_label_text("up_font6", f"UP:   {self.get_upload_speed()} MB")
        self.update_label_text("down_font6", f"DOWN: {self.get_download_speed()} MB")

    def task_manager_click(self):
        print("Task Manager Clicked")
        self.update_task_manager_info()
        subprocess.Popen(["powershell", "-Command", "Start-Process taskmgr -Verb runAs"])
        button = next(b for b in self.buttons if b.command == self.task_manager_click)
        for widget, value in button.widget_info.items():
            print(f"  {widget}: {value}")

"""