import re
import tkinter as tk
from tkinter import ttk

LIGHT_COLORS = {
    'clean': {
        'label_bg': "#e1e1e1",
        'hover_bg': "#c7e0f4",
        'click_bg': "#a9d1f5",
        'border_color': "#adadad",
        'hover_border': "#0078d7",
        'click_border': "#005499",
        'text_color': "#000000",
        'text_bg': "#ffffff",
        'labelframe_bg': "#f0f0f0",
        'labelframe_fg': "#333333"
    },
    'retro': {
        'label_bg': "#f0f0f0",
        'hover_bg': "#e0e0e0",
        'click_bg': "#d0d0d0",
        'border_color': "#c0c0c0",
        'hover_border': "#a0a0a0",
        'click_border': "#808080",
        'text_color': "#000000",
        'text_bg': "#ffffff",
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
        'text_bg': "#181818",
        'labelframe_bg': "#383838",
        'labelframe_fg': "#ffffff"
    },
    'retro': {
        'label_bg': "#404040",
        'hover_bg': "#505050",
        'click_bg': "#606060",
        'border_color': "#808080",
        'hover_border': "#a0a0a0",
        'click_border': "#c0c0c0",
        'text_color': "#ffffff",
        'text_bg': "#181818",
        'labelframe_bg': "#505050",
        'labelframe_fg': "#ffffff"
    }
}

class FancyButtonStyleLibrary:
    def __init__(self):
        self.style = ttk.Style()

    def get_colors(self, theme, mode):
        return DARK_COLORS[theme] if mode == "dark" else LIGHT_COLORS[theme]

    def get_font_size(self, widget):
        name = widget.winfo_name()
        font_match = re.search(r'font(\d+)', name)
        size = int(font_match.group(1)) if font_match else 10
        print(f"Widget: {name}, Font size: {size}")
        return size

    def style_widget(self, widget, theme, mode):
        widget_class = widget.winfo_class()
        if isinstance(widget, tk.Widget):
            if widget_class == "Listbox":
                self.style_tk_listbox(widget, theme, mode)
            elif widget_class == "Label":
                self.style_tk_label(widget, theme, mode)
            elif widget_class == "Button":
                self.style_tk_button(widget, theme, mode)
            elif widget_class == "Entry":
                self.style_tk_entry(widget, theme, mode)
            elif widget_class == "Text":
                self.style_tk_text(widget, theme, mode)
            elif widget_class == "Frame":
                self.style_tk_frame(widget, theme, mode)
            elif widget_class == "Canvas":
                self.style_tk_canvas(widget, theme, mode)
        elif isinstance(widget, ttk.Widget):
            if widget_class == "TFrame":
                self.style_ttk_frame(widget, theme, mode)
            elif widget_class == "TLabel":
                self.style_ttk_label(widget, theme, mode)
            elif widget_class == "TButton":
                self.style_ttk_button(widget, theme, mode)
            elif widget_class == "TEntry":
                self.style_ttk_entry(widget, theme, mode)
            elif widget_class == "TCheckbutton":
                self.style_ttk_checkbutton(widget, theme, mode)
            elif widget_class == "TRadiobutton":
                self.style_ttk_radiobutton(widget, theme, mode)
            elif widget_class == "TCombobox":
                self.style_ttk_combobox(widget, theme, mode)
            elif widget_class == "Treeview":
                self.style_ttk_treeview(widget, theme, mode)

    def style_tk_listbox(self, widget, theme, mode):
        colors = self.get_colors(theme, mode)
        widget.configure(
            background=colors['text_bg'],
            foreground=colors['text_color'],
            selectbackground=colors['hover_bg'],
            selectforeground=colors['text_color'],
            font=("TkDefaultFont", self.get_font_size(widget)),
            borderwidth=2 if theme == 'retro' else 1,
            relief="sunken"
        )

    def style_tk_label(self, widget, theme, mode, state="normal"):
        colors = self.get_colors(theme, mode)
        bg_color = colors['hover_bg'] if state == "hover" else colors['click_bg'] if state == "click" else colors['label_bg']
        widget.configure(
            background=bg_color,
            foreground=colors['text_color'],
            font=("TkDefaultFont", self.get_font_size(widget))
        )

    def style_tk_button(self, widget, theme, mode):
        colors = self.get_colors(theme, mode)
        widget.configure(
            background=colors['label_bg'],
            foreground=colors['text_color'],
            activebackground=colors['hover_bg'],
            activeforeground=colors['text_color'],
            font=("TkDefaultFont", self.get_font_size(widget)),
            relief="raised" if theme == 'retro' else "flat",
            borderwidth=2 if theme == 'retro' else 1
        )

    def style_tk_entry(self, widget, theme, mode):
        colors = self.get_colors(theme, mode)
        widget.configure(
            background=colors['text_bg'],
            foreground=colors['text_color'],
            insertbackground=colors['text_color'],
            selectbackground=colors['hover_bg'],
            selectforeground=colors['text_color'],
            font=("TkDefaultFont", self.get_font_size(widget)),
            relief="sunken",
            borderwidth=2 if theme == 'retro' else 1
        )

    def style_tk_text(self, widget, theme, mode):
        colors = self.get_colors(theme, mode)
        widget.configure(
            background=colors['text_bg'],
            foreground=colors['text_color'],
            insertbackground=colors['text_color'],
            selectbackground=colors['hover_bg'],
            selectforeground=colors['text_color'],
            font=("TkDefaultFont", self.get_font_size(widget)),
            relief="sunken",
            borderwidth=2 if theme == 'retro' else 1
        )

    def style_tk_frame(self, widget, theme, mode):
        colors = self.get_colors(theme, mode)
        widget.configure(
            background=colors['label_bg'],
            borderwidth=0
        )

    def style_tk_canvas(self, widget, theme, mode):
        colors = self.get_colors(theme, mode)
        widget.configure(
            background=colors['label_bg'],
            highlightthickness=0
        )

    def style_ttk_frame(self, widget, theme, mode):
        colors = self.get_colors(theme, mode)
        style_name = f"{widget}.TFrame"
        self.style.configure(style_name,
            background=colors['label_bg']
        )
        widget.configure(style=style_name)

    def style_ttk_label(self, widget, theme, mode):
        colors = self.get_colors(theme, mode)
        style_name = f"{widget}.TLabel"
        self.style.configure(style_name,
            background=colors['label_bg'],
            foreground=colors['text_color'],
            font=("TkDefaultFont", self.get_font_size(widget))
        )
        self.style.map(style_name,
            background=[('active', colors['hover_bg']), ('pressed', colors['click_bg'])]
        )
        widget.configure(style=style_name)

    def style_ttk_button(self, widget, theme, mode):
        colors = self.get_colors(theme, mode)
        style_name = f"{widget}.TButton"
        self.style.configure(style_name,
            background=colors['label_bg'],
            foreground=colors['text_color'],
            font=("TkDefaultFont", self.get_font_size(widget))
        )
        self.style.map(style_name,
            background=[('active', colors['hover_bg']), ('pressed', colors['click_bg'])],
            relief=[('pressed', 'sunken')]
        )
        widget.configure(style=style_name)

    def style_ttk_entry(self, widget, theme, mode):
        colors = self.get_colors(theme, mode)
        style_name = f"{widget}.TEntry"
        self.style.configure(style_name,
            background=colors['text_bg'],
            foreground=colors['text_color'],
            fieldbackground=colors['text_bg'],
            font=("TkDefaultFont", self.get_font_size(widget))
        )
        self.style.map(style_name,
            fieldbackground=[('readonly', colors['label_bg'])]
        )
        widget.configure(style=style_name)

    def style_ttk_checkbutton(self, widget, theme, mode):
        colors = self.get_colors(theme, mode)
        style_name = f"{widget}.TCheckbutton"
        self.style.configure(style_name,
            background=colors['label_bg'],
            foreground=colors['text_color'],
            font=("TkDefaultFont", self.get_font_size(widget))
        )
        self.style.map(style_name,
            background=[('active', colors['hover_bg'])],
            foreground=[('active', colors['text_color'])]
        )
        widget.configure(style=style_name)

    def style_ttk_radiobutton(self, widget, theme, mode):
        colors = self.get_colors(theme, mode)
        style_name = f"{widget}.TRadiobutton"
        self.style.configure(style_name,
            background=colors['label_bg'],
            foreground=colors['text_color'],
            font=("TkDefaultFont", self.get_font_size(widget))
        )
        self.style.map(style_name,
            background=[('active', colors['hover_bg'])],
            foreground=[('active', colors['text_color'])]
        )
        widget.configure(style=style_name)

    def style_ttk_combobox(self, widget, theme, mode):
        colors = self.get_colors(theme, mode)
        style_name = f"{widget}.TCombobox"
        self.style.configure(style_name,
            background=colors['text_bg'],
            foreground=colors['text_color'],
            fieldbackground=colors['text_bg'],
            font=("TkDefaultFont", self.get_font_size(widget))
        )
        self.style.map(style_name,
            fieldbackground=[('readonly', colors['label_bg'])]
        )
        widget.configure(style=style_name)

    def style_ttk_treeview(self, widget, theme, mode):
        colors = self.get_colors(theme, mode)
        style_name = f"{widget}.Treeview"
        self.style.configure(style_name,
            background=colors['text_bg'],
            foreground=colors['text_color'],
            fieldbackground=colors['text_bg'],
            font=("TkDefaultFont", self.get_font_size(widget))
        )
        self.style.map(style_name,
            background=[('selected', colors['hover_bg'])],
            foreground=[('selected', colors['text_color'])]
        )
        widget.configure(style=style_name)