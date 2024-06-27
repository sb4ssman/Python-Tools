# Closest working one yet

# ISSUES:

    # CLEAR: (some of these will fix retro too)
        # The radiobutton background does not respond correctly to hover and click events.
        # The nested frame backgrounds do not respond correctly to hover and click events.
        # Checkbutton backgrounds don't respond to hover and click

    # RETRO:
        # combobox background color
        # relief shadow too dar - not equivalent to default!
        # Inner border doesn't match surface
        # 
    
    # Extra examples don't change states?
        # better examples of ways to call the fancybutton class?
    
    # Dark modes: 
        # UGLY
        # need to match their light mode counterparts better
        # should affect whole app - fancybuttons stylings should stay isolated but match the whole app. 
        # Toggle button is supposed to be the baseline for judgment of button appearance and behavior. 


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
            #         child.configure(bg=bg_color)

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

    # def style_ttk_widget(self, widget, bg_color, fg_color, state):
    #     widget_class = widget.winfo_class()
    #     theme = self.theme_var.get().lower()
    #     mode = "dark" if self.dark_mode_var.get() else "light"
    #     colors = DARK_COLORS[theme] if mode == "dark" else LIGHT_COLORS[theme]
    #     font_size = self.get_font_size(widget)

    #     if theme == "clean":
    #         if state == "Hover":
    #             bg_color = colors['hover_bg']
    #         elif state == "Click":
    #             bg_color = colors['click_bg']

    #     try:
    #         if widget_class in ['TLabel', 'TCheckbutton', 'TRadiobutton']:
    #             widget.configure(style=f'{widget_class}.{id(self)}')
    #             self.style.configure(f'{widget_class}.{id(self)}', background=bg_color, foreground=fg_color)
    #         elif widget_class in ['TEntry', 'TSpinbox', 'TCombobox']:
    #             widget.configure(style=f'{widget_class}.{id(self)}')
    #             self.style.configure(f'{widget_class}.{id(self)}', fieldbackground=bg_color, foreground=fg_color)
    #         elif widget_class == 'TScale':
    #             widget.configure(style=f'{widget_class}.{id(self)}')
    #             self.style.configure(f'{widget_class}.{id(self)}', troughcolor=bg_color)
    #         elif widget_class == 'TProgressbar':
    #             widget.configure(style=f'{widget_class}.{id(self)}')
    #             if theme == "retro":
    #                 self.style.configure(f'{widget_class}.{id(self)}', 
    #                                     background='blue', 
    #                                     troughcolor='white' if mode == "light" else 'gray')
    #             else:
    #                 self.style.configure(f'{widget_class}.{id(self)}', 
    #                                     background=bg_color, 
    #                                     troughcolor=bg_color)
    #         elif widget_class in ['TFrame', 'TLabelframe']:
    #             widget.configure(style=f'{widget_class}.{id(self)}')
    #             self.style.configure(f'{widget_class}.{id(self)}', background=bg_color)
    #     except tk.TclError:
    #         pass  # Ignore if the widget doesn't support these options

    #     # Apply font size directly to widgets that support it
    #     if widget_class in ['TLabel', 'TCheckbutton', 'TRadiobutton', 'TEntry', 'TSpinbox', 'TCombobox']:
    #         try:
    #             widget.configure(font=("TkDefaultFont", font_size))
    #         except tk.TclError:
    #             pass  # Ignore if widget doesn't support direct font configuration

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


#############################
#                           #
#   Test app and examples   #
#                           #
#############################

class FancyButtonTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FancyButton Test Application")
        self.root.geometry("420x600")

        self.radio_triggers_command = True # Set for radio buttons to trigger the fancybutton click

        self.style = ttk.Style()
        self.theme_var = tk.StringVar(value="Clean")
        self.dark_mode_var = tk.BooleanVar(value=False)
        self.style.theme_use('xpnative')

        self.main_frame = ttk.Frame(root, style='Main.TFrame')
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        self.toolbox_frame = ttk.Frame(self.main_frame, style='Toolbox.TFrame')
        self.toolbox_frame.pack(expand=True, fill=tk.BOTH, padx=0, pady=0)

        self.create_buttons()

        self.extra_examples_frame = ttk.Frame(self.main_frame, style='Toolbox.TFrame')
        self.extra_examples_frame.pack(expand=True, fill=tk.BOTH, padx=0, pady=0)

        # Example 1: Simple label as a FancyButton 
        FancyButton(self.extra_examples_frame, 
                    lambda surface: [ttk.Label(surface, text="Example Label\nMade a Button", anchor="center", name="example_label_font12").pack(expand=True, fill=tk.BOTH)], 
                    self.theme_var, self.dark_mode_var, self.example_label_click).outer_frame.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.BOTH)

        # Example 2: LabelFrame as a FancyButton
        FancyButton(self.extra_examples_frame,
                    self.create_labelframe_button_surface,
                    self.theme_var, self.dark_mode_var, self.labelframe_click).outer_frame.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.BOTH)

        # Example 3: Multiple buttons in a FancyButton
        FancyButton(self.extra_examples_frame,
                    self.create_complex_button_surface,
                    self.theme_var, self.dark_mode_var, self.complex_button_click).outer_frame.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.BOTH)

        self.controls_frame = ttk.Frame(self.main_frame, style='Control.TFrame')
        self.controls_frame.pack(pady=10)

        self.toggle_theme_button = ttk.Button(self.controls_frame, text="Toggle Theme", command=self.toggle_theme)
        self.toggle_theme_button.pack(side=tk.LEFT, padx=5)

        self.dark_mode_check = ttk.Checkbutton(self.controls_frame, text="Dark Mode", variable=self.dark_mode_var, command=self.toggle_dark_mode)
        self.dark_mode_check.pack(side=tk.LEFT, padx=5)

        self.update_app_style()

    def create_buttons(self):
        self.buttons = []
        button_configs = [
            ("taskmanager", self.create_taskmanager_surface, self.task_manager_click),
            ("prompt", self.create_prompt_surface, self.prompt_click),
            ("mouse_tracker", self.create_mouse_tracker_surface, self.mouse_tracker_click),
            ("spinbox", self.create_spinbox_surface, self.spinbox_click),
            ("radiobutton", self.create_radiobutton_surface, self.radiobutton_click),
            ("scale", self.create_scale_surface, self.scale_click),
            ("listbox", self.create_listbox_surface, self.listbox_click),
            ("canvas", self.create_canvas_surface, self.canvas_click),
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


    def create_labelframe_button_surface(self, surface):
        frame = ttk.LabelFrame(surface, text="LabelFrame Button", name="labelframe_font10")
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        ttk.Label(frame, text="Content inside\nLabelFrame", anchor="center", name="labelframe_content_font10").pack(expand=True, fill=tk.BOTH)
        return surface.winfo_children()

    def create_complex_button_surface(self, surface):
        ttk.Label(surface, text="Complex Button", name="complex_title_font12").pack(expand=True, fill=tk.BOTH)
        ttk.Label(surface, text="Inner buttons\nalso press outer.", name="complex_label_font8").pack(expand=True, fill=tk.BOTH)
        button_frame = ttk.Frame(surface)
        button_frame.pack(expand=True, fill=tk.BOTH)
        ttk.Button(button_frame, text="1", name="complex_button1_font10", width=3, command=self.inner_button1_click).pack(side=tk.LEFT, padx=2, expand=False)
        ttk.Button(button_frame, text="2", name="complex_button2_font10", width=3, command=self.inner_button2_click).pack(side=tk.RIGHT, padx=2, expand=False)
        return surface.winfo_children()


    # Some fancy button surfaces - with instance vars
    ##############################

    def create_taskmanager_surface(self, surface):
        self.tm_title = ttk.Label(surface, text="Task Manager", anchor="center", width=12, name="tm_title_font8")
        self.tm_title.pack(fill=tk.X, padx=5, pady=(2, 0))
        ttk.Separator(surface, orient="horizontal").pack(fill=tk.X, padx=5, pady=0)
        self.tm_cpu = ttk.Label(surface, text="CPU:  0%", anchor="w", name="tm_cpu_font6")
        self.tm_cpu.pack(fill=tk.X, padx=10, pady=(0, 0))
        self.tm_ram = ttk.Label(surface, text="RAM:  0%", anchor="w", name="tm_ram_font6")
        self.tm_ram.pack(fill=tk.X, padx=10, pady=0)
        self.tm_disk = ttk.Label(surface, text="DISK: 0%", anchor="w", name="tm_disk_font6")
        self.tm_disk.pack(fill=tk.X, padx=10, pady=0)
        self.tm_up = ttk.Label(surface, text="UP:   0 MB", anchor="w", name="tm_up_font6")
        self.tm_up.pack(fill=tk.X, padx=10, pady=0)
        self.tm_down = ttk.Label(surface, text="DOWN: 0 MB", anchor="w", name="tm_down_font6")
        self.tm_down.pack(fill=tk.X, padx=10, pady=(0, 2))
        return surface.winfo_children()

    def create_prompt_surface(self, surface):
        self.pc_title = ttk.Label(surface, text="Prompt Chooser", anchor="center", name="pc_title_font10")
        self.pc_title.pack(fill=tk.X, padx=5, pady=(2, 0))
        ttk.Separator(surface, orient="horizontal").pack(fill=tk.X, padx=5, pady=0)
        self.pc_combo = ttk.Combobox(surface, values=["Terminal", "PowerShell", "cmd"], state="readonly", width=10, name="pc_combo_font10")
        self.pc_combo.set("Terminal")
        self.pc_combo.pack(fill=tk.X, padx=5, pady=5)
        
        self.pc_bottom_frame = ttk.Frame(surface, name="pc_bottom_frame")
        self.pc_bottom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.admin_var = tk.BooleanVar(value=False)
        self.pc_admin_check = ttk.Checkbutton(self.pc_bottom_frame, text="Admin", variable=self.admin_var, name="pc_admin_check_font8")
        self.pc_admin_check.pack(side=tk.LEFT)
        self.pc_prompt = ttk.Label(self.pc_bottom_frame, text="PROMPT", anchor="center", name="pc_prompt_font12")
        self.pc_prompt.pack(side=tk.LEFT, padx=(5, 0))
        return surface.winfo_children()

    def create_mouse_tracker_surface(self, surface):
        self.mt_title = ttk.Label(surface, text="Mouse Tracker", anchor="center", width=12, name="mt_title_font12")
        self.mt_title.pack(fill=tk.X, padx=5, pady=(2, 0))
        ttk.Separator(surface, orient="horizontal").pack(fill=tk.X, padx=5, pady=0)
        self.mt_coordinates = ttk.Label(surface, text="Pixel:          (0, 0)\nWindows:  (0, 0)", anchor="w", name="mt_coordinates_font8")
        self.mt_coordinates.pack(fill=tk.X, padx=10, pady=2)
        self.mt_start = ttk.Label(surface, text="Start Tracking", anchor="center", name="mt_start_font10")
        self.mt_start.pack(fill=tk.BOTH, padx=5, pady=5, ipady=5)
        return surface.winfo_children()

    def create_spinbox_surface(self, surface):
        self.sb_title = ttk.Label(surface, text="Spinbox", anchor="center", name="sb_title_font12")
        self.sb_title.pack(fill=tk.X, padx=5, pady=(2, 0))
        self.sb_value = ttk.Spinbox(surface, from_=0, to=10, width=6, name="sb_value_font10")
        self.sb_value.pack(fill=tk.X, padx=5, pady=5)
        self.sb_label = ttk.Label(surface, text="Font Size 10", anchor="center", name="sb_label_font10")
        self.sb_label.pack(fill=tk.X, padx=5, pady=(2, 0))
        return surface.winfo_children()

    def create_radiobutton_surface(self, surface):
        self.rb_title = ttk.Label(surface, text="Radiobutton", anchor="center", name="rb_title_font12")
        self.rb_title.pack(fill=tk.X, padx=5, pady=(2, 0))
        self.radio_var = tk.StringVar(value="")  # No default selection
        self.rb_option1 = ttk.Radiobutton(surface, text="Option 1", variable=self.radio_var, value="Option 1", name="rb_option1_font8", 
                        command=self.on_radio_click if self.radio_triggers_command else None)
        self.rb_option1.pack(fill=tk.X, padx=5, pady=5)
        self.rb_option2 = ttk.Radiobutton(surface, text="Option 2", variable=self.radio_var, value="Option 2", name="rb_option2_font12", 
                        command=self.on_radio_click if self.radio_triggers_command else None)
        self.rb_option2.pack(fill=tk.X, padx=5, pady=5)
        self.rb_label = ttk.Label(surface, text="Font Size 6", anchor="center", name="rb_label_font6")
        self.rb_label.pack(fill=tk.X, padx=5, pady=(2, 0))
        return surface.winfo_children()

    def create_scale_surface(self, surface):
        self.sc_title = ttk.Label(surface, text="Scale", anchor="center", name="sc_title_font12")
        self.sc_title.pack(fill=tk.X, padx=5, pady=(2, 0))
        self.sc_value = ttk.Scale(surface, from_=0, to=100, name="sc_value_font10")
        self.sc_value.pack(fill=tk.X, padx=5, pady=5)
        self.sc_label = ttk.Label(surface, text="Font Size 10", anchor="center", name="sc_label_font10")
        self.sc_label.pack(fill=tk.X, padx=5, pady=(2, 0))
        return surface.winfo_children()

    def create_listbox_surface(self, surface):
        self.lb_title = ttk.Label(surface, text="Listbox", anchor="center", name="lb_title_font12")
        self.lb_title.pack(fill=tk.X, padx=5, pady=(2, 0))
        frame = ttk.Frame(surface)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.lb_items = tk.Listbox(frame, width=10, height=5, name="lb_items_font8")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.lb_items.yview)
        self.lb_items.config(yscrollcommand=scrollbar.set)
        self.lb_items.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        for i in range(1, 21):
            self.lb_items.insert(tk.END, f"Item {i}")
        self.lb_label = ttk.Label(surface, text="Font Size 8", anchor="center", name="lb_label_font8")
        self.lb_label.pack(fill=tk.X, padx=5, pady=(2, 0))
        return surface.winfo_children()

    def create_canvas_surface(self, surface):
        self.cv_title = ttk.Label(surface, text="Canvas", anchor="center", name="cv_title_font12")
        self.cv_title.pack(fill=tk.X, padx=5, pady=(2, 0))
        self.cv_main = tk.Canvas(surface, width=100, height=50, bg="white", name="cv_main")
        self.cv_main.pack(fill=tk.X, padx=5, pady=5)
        self.cv_main.create_oval(10, 10, 90, 40, fill="blue")
        self.cv_label = ttk.Label(surface, text="Font Size 12", anchor="center", name="cv_label_font12")
        self.cv_label.pack(fill=tk.X, padx=5, pady=(2, 0))
        return surface.winfo_children()

    def create_progressbar_surface(self, surface):
        self.pb_title = ttk.Label(surface, text="Progressbar", anchor="center", name="pb_title_font12")
        self.pb_title.pack(fill=tk.X, padx=5, pady=(2, 0))
        self.pb_main = ttk.Progressbar(surface, value=50, name="pb_main")
        self.pb_main.pack(fill=tk.X, padx=5, pady=5)
        
        self.pb_entry = ttk.Entry(surface, name="pb_entry_font10")
        self.pb_entry.insert(0, "Neat!")  # Set default text
        self.pb_entry.pack(fill=tk.X, padx=5, pady=5)
        
        self.pb_label = ttk.Label(surface, text="Font Size 10", anchor="center", name="pb_label_font10")
        self.pb_label.pack(fill=tk.X, padx=5, pady=(2, 0))
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
        self.create_extra_examples()  # Recreate the extra examples

    def example_label_click(self):
        print("Example Label Clicked")

    def labelframe_click(self):
        print("LabelFrame Clicked")
    
    def complex_button_click(self):
        print("Complex Button Clicked")
        # Find the button in the extra examples
        button = next((b for b in self.extra_examples_frame.winfo_children() if isinstance(b, FancyButton) and b.command == self.complex_button_click), None)
        if button:
            for widget, value in button.widget_info.items():
                print(f"  {widget}: {value}")
        else:
            print("  Complex button not found")
    
    def inner_button1_click(self):
        print("Inner Button 1 Clicked")

    def inner_button2_click(self):
        print("Inner Button 2 Clicked")

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
        
        # Get the selected item directly from the listbox
        selection = self.lb_items.curselection()
        if selection:
            selected_item = self.lb_items.get(selection[0])
            print(f"  Selected item: {selected_item}")
        else:
            print("  No item selected")

        # Print other widget info if any
        for widget, value in button.widget_info.items():
            if widget != "lb_items_font8":
                print(f"  {widget}: {value}")
                
    def canvas_click(self):
        print("Canvas Button Clicked")
        button = next(b for b in self.buttons if b.command == self.canvas_click)
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