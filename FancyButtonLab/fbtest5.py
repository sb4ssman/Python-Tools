# Another crappy test




import tkinter as tk
from tkinter import ttk
import subprocess


# Shared color scheme
LIGHT_COLORS = {
    'clean': {
        'label_bg': "#e1e1e1",
        'hover_bg': "#e5f1fb",
        'click_bg': "#cce4f7",
        'border_color': "#adadad",
        'hover_border': "#0078d7",
        'click_border': "#005499"
    },
    'retro': {
        'label_bg': "#f0f0f0",
        'hover_bg': "#e8e8e8",
        'click_bg': "#d0d0d0",
        'border_color': "#a0a0a0",
        'hover_border': "#808080",
        'click_border': "#606060"
    }
}

DARK_COLORS = {
    'clean': {
        'label_bg': "#2d2d2d",
        'hover_bg': "#3a3a3a",
        'click_bg': "#454545",
        'border_color': "#555555",
        'hover_border': "#777777",
        'click_border': "#999999"
    },
    'retro': {
        'label_bg': "#1f1f1f",
        'hover_bg': "#2a2a2a",
        'click_bg': "#353535",
        'border_color': "#4a4a4a",
        'hover_border': "#5a5a5a",
        'click_border': "#6a6a6a"
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
        self.initialize_styles()

        self.outer_frame = tk.Frame(self.parent, bd=0, highlightthickness=0)
        self.inner_frame = tk.Frame(self.outer_frame, bd=0, highlightthickness=0)
        self.inner_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        self.surface = tk.Frame(self.inner_frame, bd=0, highlightthickness=0)
        self.surface.pack(fill=tk.BOTH, expand=False, padx=0, pady=0)

        self.widgets = {}
        self.font_sizes = {}
        self.create_surface(self.surface)

        self.is_hovered = False
        self.bind_events()
        self.update_style("")

    def initialize_styles(self):
        for theme in ['clean', 'retro']:
            for mode in ['light', 'dark']:
                colors = DARK_COLORS[theme] if mode == 'dark' else LIGHT_COLORS[theme]
                bg_color = colors['label_bg']
                fg_color = "white" if mode == 'dark' else "black"
                
                for widget_type in ['TLabel', 'TButton', 'TCheckbutton', 'TRadiobutton', 'TEntry', 'TSpinbox', 'TCombobox', 'TScale', 'TProgressbar']:
                    style_name = f"Custom.{widget_type}.{theme}.{mode}"
                    if widget_type in ['TEntry', 'TSpinbox', 'TCombobox']:
                        self.style.configure(style_name, fieldbackground=bg_color, foreground=fg_color)
                    elif widget_type == 'TProgressbar':
                        self.style.configure(style_name, background=bg_color, troughcolor=colors.get('border_color', bg_color))
                    else:
                        self.style.configure(style_name, background=bg_color, foreground=fg_color)
                
                for font_size in [6, 8, 10, 12]:
                    style_name = f"Custom.TLabel.{theme}.{mode}.font{font_size}"
                    self.style.configure(style_name, font=("", font_size))

    def bind_events(self):
        self.outer_frame.bind("<Enter>", self.on_enter)
        self.outer_frame.bind("<Leave>", self.on_leave)
        self.outer_frame.bind("<Button-1>", self.on_click)
        self.outer_frame.bind("<ButtonRelease-1>", self.on_release)
        self.bind_children(self.surface)

    def bind_children(self, widget):
        for child in widget.winfo_children():
            child.bind("<Enter>", self.on_enter_child)
            child.bind("<Leave>", self.on_leave_child)
            if not isinstance(child, (ttk.Entry, ttk.Spinbox, ttk.Combobox, ttk.Scale)):
                child.bind("<Button-1>", self.on_click_child)
                child.bind("<ButtonRelease-1>", self.on_release_child)
            self.bind_children(child)

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

    def on_release(self, event):
        if self.is_mouse_within_bounds(event.x_root, event.y_root):
            self.command()
        self.update_style("Hover" if self.is_hovered else "")

    def on_click_child(self, event):
        self.update_style("Click")

    def on_release_child(self, event):
        if self.is_mouse_within_bounds(event.x_root, event.y_root):
            self.command()
        self.update_style("Hover" if self.is_hovered else "")

    def update_style(self, state):
        theme = self.theme_var.get().lower()
        mode = "dark" if self.dark_mode_var.get() else "light"
        colors = DARK_COLORS[theme] if mode == "dark" else LIGHT_COLORS[theme]

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
            if state == "Hover":
                self.outer_frame.config(bd=2, relief="raised")
                self.inner_frame.config(bg=colors['hover_bg'])
            elif state == "Click":
                self.outer_frame.config(bd=2, relief="sunken")
                self.inner_frame.config(bg=colors['click_bg'])
            else:
                self.outer_frame.config(bd=2, relief="raised")
                self.inner_frame.config(bg=colors['label_bg'])

        self.surface.config(bg=self.inner_frame.cget("bg"))
        self.style_descendants(self.surface, theme, mode, state)

    def style_descendants(self, widget, theme, mode, state):
        colors = DARK_COLORS[theme] if mode == "dark" else LIGHT_COLORS[theme]
        bg_color = colors[f"{'label' if state == '' else state.lower()}_bg"]
        fg_color = "white" if mode == "dark" else "black"

        for name, child in self.widgets.items():
            if isinstance(child, ttk.Label):
                font_size = self.font_sizes.get(name, 8)  # Default to 8 if not specified
                style_name = f"Custom.TLabel.{theme}.{mode}.font{font_size}"
                child.configure(style=style_name)
            elif isinstance(child, ttk.Entry):
                child.configure(style=f"Custom.TEntry.{theme}.{mode}")
            elif isinstance(child, ttk.Spinbox):
                child.configure(style=f"Custom.TSpinbox.{theme}.{mode}")
            elif isinstance(child, ttk.Combobox):
                child.configure(style=f"Custom.TCombobox.{theme}.{mode}")
            elif isinstance(child, ttk.Scale):
                child.configure(style=f"Custom.Horizontal.TScale.{theme}.{mode}")
            elif isinstance(child, tk.Canvas):
                child.configure(bg=bg_color)


    # def style_label(self, label, theme, mode, state, colors):
    #     bg_color = colors[f"{'label' if state == '' else state.lower()}_bg"]
    #     fg_color = "black" if mode == "light" else "white"
    #     label.configure(background=bg_color, foreground=fg_color)

    # def style_button(self, button, theme, mode, state, colors):
    #     style_name = f"Custom.TButton.{theme}.{mode}"
    #     button.configure(style=style_name)

    # def style_checkbutton(self, checkbutton, theme, mode, state, colors):
    #     style_name = f"Custom.TCheckbutton.{theme}.{mode}"
    #     checkbutton.configure(style=style_name)

    # def style_radiobutton(self, radiobutton, theme, mode, state, colors):
    #     style_name = f"Custom.TRadiobutton.{theme}.{mode}"
    #     radiobutton.configure(style=style_name)

    # def style_combobox(self, combobox, theme, mode, state, colors):
    #     style_name = f"Custom.TCombobox.{theme}.{mode}"
    #     combobox.configure(style=style_name)

    # def style_entry(self, entry, theme, mode, state, colors):
    #     style_name = f"Custom.TEntry.{theme}.{mode}"
    #     entry.configure(style=style_name)

    # def style_spinbox(self, spinbox, theme, mode, state, colors):
    #     style_name = f"Custom.TSpinbox.{theme}.{mode}"
    #     spinbox.configure(style=style_name)

    # def style_scale(self, scale, theme, mode, state, colors):
    #     style_name = f"Custom.Horizontal.TScale.{theme}.{mode}"
    #     scale.configure(style=style_name)

    # def style_progressbar(self, progressbar, theme, mode, state, colors):
    #     style_name = f"Custom.Horizontal.TProgressbar.{theme}.{mode}"
    #     progressbar.configure(style=style_name)

    # def style_listbox(self, listbox, theme, mode, state, colors):
    #     bg_color = colors[f"{'label' if state == '' else state.lower()}_bg"]
    #     fg_color = "black" if mode == "light" else "white"
    #     listbox.configure(bg=bg_color, fg=fg_color)

    # def style_canvas(self, canvas, theme, mode, state, colors):
    #     bg_color = colors[f"{'label' if state == '' else state.lower()}_bg"]
    #     canvas.configure(bg=bg_color)

    def is_mouse_within_bounds(self, x_root, y_root):
        left = self.outer_frame.winfo_rootx()
        right = left + self.outer_frame.winfo_width()
        top = self.outer_frame.winfo_rooty()
        bottom = top + self.outer_frame.winfo_height()
        return left <= x_root <= right and top <= y_root <= bottom

    def recreate(self):
        self.outer_frame.destroy()
        self.__init__(self.parent, self.create_surface, self.theme_var, self.dark_mode_var, self.command)



class FancyButtonTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FancyButton Test Application")
        self.root.geometry("800x600")

        self.style = ttk.Style()
        self.theme_var = tk.StringVar(value="Clean")
        self.dark_mode_var = tk.BooleanVar(value=False)
        self.style.theme_use('xpnative')

        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        self.toolbox_frame = ttk.Frame(self.main_frame)
        self.toolbox_frame.pack(expand=True, fill=tk.BOTH)

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

        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(pady=10)

        self.toggle_theme_button = ttk.Button(control_frame, text="Toggle Theme", command=self.toggle_theme)
        self.toggle_theme_button.pack(side=tk.LEFT, padx=5)

        self.dark_mode_check = ttk.Checkbutton(control_frame, text="Dark Mode", variable=self.dark_mode_var, command=self.toggle_dark_mode)
        self.dark_mode_check.pack(side=tk.LEFT, padx=5)


    def initialize_styles(self):
        style = self.style
        for theme in ['clean', 'retro']:
            for mode in ['light', 'dark']:
                colors = LIGHT_COLORS[theme] if mode == 'light' else DARK_COLORS[theme]
                bg_color = colors['label_bg']
                fg_color = "black" if mode == 'light' else "white"
                
                for widget_type in ['TButton', 'TRadiobutton', 'TCheckbutton', 'TCombobox', 'TEntry', 'TSpinbox', 'Scale', 'Progressbar']:
                    style_name = f"Custom.{widget_type}.{theme}.{mode}"
                    if widget_type in ['TCombobox', 'TEntry', 'TSpinbox']:
                        style.configure(style_name, fieldbackground=bg_color, foreground=fg_color)
                    elif widget_type == 'Progressbar':
                        style.configure(style_name, background=bg_color, troughcolor=colors.get('border_color', bg_color))
                    else:
                        style.configure(style_name, background=bg_color, foreground=fg_color)



    def create_taskmanager_surface(surface):
        widgets = {}
        font_sizes = {}

        widgets['title'] = ttk.Label(surface, text="Task Manager", anchor="center", width=12)
        font_sizes['title'] = 8

        widgets['sep'] = ttk.Separator(surface, orient="horizontal")

        widgets['cpu'] = ttk.Label(surface, text="CPU:  0%", anchor="w")
        font_sizes['cpu'] = 6

        widgets['ram'] = ttk.Label(surface, text="RAM:  0%", anchor="w")
        font_sizes['ram'] = 6

        widgets['disk'] = ttk.Label(surface, text="DISK: 0%", anchor="w")
        font_sizes['disk'] = 6

        widgets['up'] = ttk.Label(surface, text="UP:   0 MB", anchor="w")
        font_sizes['up'] = 6

        widgets['down'] = ttk.Label(surface, text="DOWN: 0 MB", anchor="w")
        font_sizes['down'] = 6

        widgets['title'].pack(fill=tk.X, padx=5, pady=(2, 0))
        widgets['sep'].pack(fill=tk.X, padx=5, pady=0)
        widgets['cpu'].pack(fill=tk.X, padx=10, pady=(0, 0))
        widgets['ram'].pack(fill=tk.X, padx=10, pady=0)
        widgets['disk'].pack(fill=tk.X, padx=10, pady=0)
        widgets['up'].pack(fill=tk.X, padx=10, pady=0)
        widgets['down'].pack(fill=tk.X, padx=10, pady=(0, 2))

        return widgets, font_sizes

    def create_prompt_surface(surface):
        widgets = {}
        font_sizes = {}

        widgets['title'] = ttk.Label(surface, text="Prompt Chooser", anchor="center")
        font_sizes['title'] = 12

        widgets['sep'] = ttk.Separator(surface, orient="horizontal")

        widgets['dropdown'] = ttk.Combobox(surface, textvariable=tk.StringVar(value="Terminal"), 
                                        values=["Terminal", "PowerShell", "cmd"], state="readonly", width=10)

        widgets['admin_check'] = ttk.Checkbutton(surface, text="Admin", variable=tk.IntVar())

        widgets['prompt_label'] = ttk.Label(surface, text="Prompt", anchor="center")
        font_sizes['prompt_label'] = 10

        widgets['title'].pack(fill=tk.X, padx=5, pady=(2, 0))
        widgets['sep'].pack(fill=tk.X, padx=5, pady=0)
        widgets['dropdown'].pack(fill=tk.X, padx=5, pady=5)
        widgets['admin_check'].pack(fill=tk.X, padx=5, pady=5)
        widgets['prompt_label'].pack(fill=tk.BOTH, padx=5, pady=5, ipady=5)

        return widgets, font_sizes

    def create_mouse_tracker_surface(surface):
        widgets = {}
        font_sizes = {}

        widgets['title'] = ttk.Label(surface, text="Mouse Tracker", anchor="center", width=12)
        font_sizes['title'] = 12

        widgets['sep'] = ttk.Separator(surface, orient="horizontal")

        widgets['pixel'] = ttk.Label(surface, text=f"Pixel:          (0, 0)\nWindows:  (0, 0)", anchor="w")
        font_sizes['pixel'] = 10

        widgets['start'] = ttk.Label(surface, text="Start Tracking", anchor="center")
        font_sizes['start'] = 10

        widgets['title'].pack(fill=tk.X, padx=5, pady=(2, 0))
        widgets['sep'].pack(fill=tk.X, padx=5, pady=0)
        widgets['pixel'].pack(fill=tk.X, padx=10, pady=2)
        widgets['start'].pack(fill=tk.BOTH, padx=5, pady=5, ipady=5)

        return widgets, font_sizes

    def create_spinbox_surface(surface):
        widgets = {}
        font_sizes = {}

        widgets['title'] = ttk.Label(surface, text="Spinbox", anchor="center")
        font_sizes['title'] = 12

        widgets['spinbox'] = ttk.Spinbox(surface, from_=0, to=10, width=6)

        widgets['label'] = ttk.Label(surface, text="Font Size 10", anchor="center")
        font_sizes['label'] = 10

        widgets['title'].pack(fill=tk.X, padx=5, pady=(2, 0))
        widgets['spinbox'].pack(fill=tk.X, padx=5, pady=5)
        widgets['label'].pack(fill=tk.X, padx=5, pady=(2, 0))

        return widgets, font_sizes

    def create_radiobutton_surface(surface):
        widgets = {}
        font_sizes = {}

        widgets['title'] = ttk.Label(surface, text="Radiobutton", anchor="center")
        font_sizes['title'] = 12

        radio_var = tk.StringVar()
        widgets['option1'] = ttk.Radiobutton(surface, text="Option 1", variable=radio_var, value="Option 1")
        widgets['option2'] = ttk.Radiobutton(surface, text="Option 2", variable=radio_var, value="Option 2")

        widgets['label'] = ttk.Label(surface, text="Font Size 10", anchor="center")
        font_sizes['label'] = 10

        widgets['title'].pack(fill=tk.X, padx=5, pady=(2, 0))
        widgets['option1'].pack(fill=tk.X, padx=5, pady=5)
        widgets['option2'].pack(fill=tk.X, padx=5, pady=5)
        widgets['label'].pack(fill=tk.X, padx=5, pady=(2, 0))

        return widgets, font_sizes

    def create_scale_surface(surface):
        widgets = {}
        font_sizes = {}

        widgets['title'] = ttk.Label(surface, text="Scale", anchor="center")
        font_sizes['title'] = 12

        widgets['scale'] = ttk.Scale(surface, from_=0, to=100)

        widgets['label'] = ttk.Label(surface, text="Font Size 10", anchor="center")
        font_sizes['label'] = 10

        widgets['title'].pack(fill=tk.X, padx=5, pady=(2, 0))
        widgets['scale'].pack(fill=tk.X, padx=5, pady=5)
        widgets['label'].pack(fill=tk.X, padx=5, pady=(2, 0))

        return widgets, font_sizes

    def create_listbox_surface(surface):
        widgets = {}
        font_sizes = {}

        widgets['title'] = ttk.Label(surface, text="Listbox", anchor="center")
        font_sizes['title'] = 12

        frame = ttk.Frame(surface)
        widgets['listbox'] = tk.Listbox(frame, width=10, height=5)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=widgets['listbox'].yview)
        widgets['listbox'].config(yscrollcommand=scrollbar.set)

        widgets['label'] = ttk.Label(surface, text="Font Size 10", anchor="center")
        font_sizes['label'] = 10

        widgets['title'].pack(fill=tk.X, padx=5, pady=(2, 0))
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        widgets['listbox'].pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        widgets['label'].pack(fill=tk.X, padx=5, pady=(2, 0))

        for i in range(1, 21):
            widgets['listbox'].insert(tk.END, f"Item {i}")

        return widgets, font_sizes

    def create_canvas_surface(surface):
        widgets = {}
        font_sizes = {}

        widgets['title'] = ttk.Label(surface, text="Canvas", anchor="center")
        font_sizes['title'] = 12

        widgets['canvas'] = tk.Canvas(surface, width=100, height=50, bg="white")

        widgets['label'] = ttk.Label(surface, text="Font Size 10", anchor="center")
        font_sizes['label'] = 10

        widgets['title'].pack(fill=tk.X, padx=5, pady=(2, 0))
        widgets['canvas'].pack(fill=tk.X, padx=5, pady=5)
        widgets['label'].pack(fill=tk.X, padx=5, pady=(2, 0))

        widgets['canvas'].create_oval(10, 10, 90, 40, fill="blue")

        return widgets, font_sizes

    def create_progressbar_surface(surface):
        widgets = {}
        font_sizes = {}

        widgets['title'] = ttk.Label(surface, text="Progressbar", anchor="center")
        font_sizes['title'] = 12

        widgets['progressbar'] = ttk.Progressbar(surface, value=50)

        widgets['label'] = ttk.Label(surface, text="Font Size 10", anchor="center")
        font_sizes['label'] = 10

        widgets['title'].pack(fill=tk.X, padx=5, pady=(2, 0))
        widgets['progressbar'].pack(fill=tk.X, padx=5, pady=5)
        widgets['label'].pack(fill=tk.X, padx=5, pady=(2, 0))

        return widgets, font_sizes

    def recreate_buttons(self):
        for attr in dir(self):
            if attr.endswith('_button') and hasattr(getattr(self, attr), 'recreate'):
                getattr(self, attr).recreate()

    def toggle_theme(self):
        if self.theme_var.get() == "Clean":
            self.theme_var.set("Retro")
            self.style.theme_use('winnative')
        else:
            self.theme_var.set("Clean")
            self.style.theme_use('xpnative')
        self.recreate_buttons()

    def toggle_dark_mode(self):
        self.recreate_buttons()

    def recreate_buttons(self):
        for button in self.buttons:
            button.recreate()

    def task_manager_click(self):
        print("Task Manager Clicked")
        subprocess.Popen(["powershell", "-Command", "Start-Process taskmgr -Verb runAs"])

    def prompt_click(self):
        print("Prompt Chooser Clicked")

    def mouse_tracker_click(self):
        print("Mouse Tracker Clicked")

    def spinbox_click(self):
        print("Spinbox Button Clicked")

    def radiobutton_click(self):
        print("Radiobutton Button Clicked")

    def scale_click(self):
        print("Scale Button Clicked")

    def listbox_click(self):
        print("Listbox Button Clicked")

    def canvas_click(self):
        print("Canvas Button Clicked")

    def progressbar_click(self):
        print("Progressbar Button Clicked")

if __name__ == "__main__":
    root = tk.Tk()
    app = FancyButtonTestApp(root)
    root.mainloop()