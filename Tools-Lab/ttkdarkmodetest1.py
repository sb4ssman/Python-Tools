import tkinter as tk
from tkinter import ttk


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # root window
        self.title('Theme Demo')
        self.geometry('800x600')
        self.style = ttk.Style(self)

        # Set default theme to xpnative
        default_theme = 'xpnative'
        self.style.theme_use(default_theme)

        # notebook
        notebook = ttk.Notebook(self)
        notebook.pack(padx=10, pady=10, fill='both', expand=True)

        # Create frames for each section
        self.create_basic_widgets_frame(notebook)
        self.create_advanced_widgets_frame(notebook)

        # radio button for themes
        self.selected_theme = tk.StringVar()
        theme_frame = ttk.LabelFrame(self, text='Themes and Dark Mode')
        theme_frame.pack(padx=10, pady=10, ipadx=10, ipady=10, fill='x')

        self.selected_theme.set(default_theme)

        for theme_name in self.style.theme_names():
            rb = ttk.Radiobutton(
                theme_frame,
                text=theme_name,
                value=theme_name,
                variable=self.selected_theme,
                command=self.change_theme)
            rb.pack(anchor='w', padx=5, pady=2)

        # Dark mode switch
        self.dark_mode = tk.BooleanVar()
        dark_mode_switch = ttk.Checkbutton(
            theme_frame, text='Enable Dark Mode', variable=self.dark_mode, command=self.toggle_dark_mode)
        dark_mode_switch.pack(anchor='w', padx=5, pady=2)

    def create_basic_widgets_frame(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text='Basic Widgets')

        basic_label = ttk.Label(frame, text='Basic Widgets:')
        basic_label.grid(column=0, row=0, padx=10, pady=10, sticky='w')

        # Label
        label = ttk.Label(frame, text='Name:')
        label.grid(column=0, row=1, padx=10, pady=10, sticky='w')

        # Entry
        textbox = ttk.Entry(frame)
        textbox.grid(column=1, row=1, padx=10, pady=10, sticky='w')

        # Button
        btn = ttk.Button(frame, text='Show')
        btn.grid(column=2, row=1, padx=10, pady=10, sticky='w')

        # Checkbutton
        checkbtn = ttk.Checkbutton(frame, text='Check me')
        checkbtn.grid(column=0, row=2, padx=10, pady=10, sticky='w')

        # Combobox
        combobox = ttk.Combobox(frame, values=['Option 1', 'Option 2', 'Option 3'])
        combobox.grid(column=1, row=2, padx=10, pady=10, sticky='w')

    def create_advanced_widgets_frame(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text='Advanced Widgets')

        advanced_label = ttk.Label(frame, text='Advanced Widgets:')
        advanced_label.grid(column=0, row=0, padx=10, pady=10, sticky='w')

        # Spinbox
        spinbox = ttk.Spinbox(frame, from_=0, to=10)
        spinbox.grid(column=0, row=1, padx=10, pady=10, sticky='w')

        # Scale
        scale = ttk.Scale(frame, orient='horizontal')
        scale.grid(column=1, row=1, columnspan=3, padx=10, pady=10, sticky='we')

        # Progressbar
        progressbar = ttk.Progressbar(frame, mode='determinate', value=50)
        progressbar.grid(column=0, row=2, columnspan=3, padx=10, pady=10, sticky='we')

        # Radiobuttons
        radiobutton1 = ttk.Radiobutton(frame, text='Option 1', value='1')
        radiobutton2 = ttk.Radiobutton(frame, text='Option 2', value='2')
        radiobutton1.grid(column=0, row=3, padx=10, pady=10, sticky='w')
        radiobutton2.grid(column=1, row=3, padx=10, pady=10, sticky='w')

        # Separator
        separator = ttk.Separator(frame, orient='horizontal')
        separator.grid(column=0, row=4, columnspan=3, padx=10, pady=10, sticky='we')

    def change_theme(self):
        self.style.theme_use(self.selected_theme.get())
        self.toggle_dark_mode()  # Apply dark mode settings if enabled

    def toggle_dark_mode(self):
        if self.dark_mode.get():
            self.apply_dark_mode()
        else:
            self.apply_light_mode()

    def apply_dark_mode(self):
        # Dark mode settings
        self.style.configure('.', background='#333333', foreground='#f2f2f2')
        self.style.configure('TLabel', background='#333333', foreground='#f2f2f2')
        self.style.configure('TEntry', background='#555555', foreground='#f2f2f2', fieldbackground='#666666')
        self.style.configure('TButton', background='#444444', foreground='#f2f2f2')
        self.style.configure('TCheckbutton', background='#333333', foreground='#f2f2f2')
        self.style.configure('TCombobox', background='#555555', foreground='#f2f2f2', fieldbackground='#666666')
        self.style.configure('TSpinbox', background='#555555', foreground='#f2f2f2', fieldbackground='#666666')
        self.style.configure('TScale', background='#333333', troughcolor='#666666', slidercolor='#444444')
        self.style.configure('TProgressbar', background='#666666')
        self.style.configure('TRadiobutton', background='#333333', foreground='#f2f2f2')
        self.style.configure('TSeparator', background='#666666')
        self.style.configure('TNotebook', background='#333333', foreground='#f2f2f2')
        self.style.configure('TNotebook.Tab', background='#444444', foreground='#f2f2f2')

    def apply_light_mode(self):
        # Reset to default light mode styles
        self.style.configure('.', background='', foreground='')
        self.style.configure('TLabel', background='', foreground='')
        self.style.configure('TEntry', background='', foreground='', fieldbackground='')
        self.style.configure('TButton', background='', foreground='')
        self.style.configure('TCheckbutton', background='', foreground='')
        self.style.configure('TCombobox', background='', foreground='', fieldbackground='')
        self.style.configure('TSpinbox', background='', foreground='', fieldbackground='')
        self.style.configure('TScale', background='', troughcolor='', slidercolor='')
        self.style.configure('TProgressbar', background='')
        self.style.configure('TRadiobutton', background='', foreground='')
        self.style.configure('TSeparator', background='')
        self.style.configure('TNotebook', background='', foreground='')
        self.style.configure('TNotebook.Tab', background='', foreground='')


if __name__ == "__main__":
    app = App()
    app.mainloop()
