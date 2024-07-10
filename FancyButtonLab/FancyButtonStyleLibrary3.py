# -*- coding: utf-8 -*-
"""
Created on Thu Jul 4 11:22:38 2024

@author: Thomas
"""


# Accompanies FancyButton Class
# Covers 4 states: Retro/Clean-Light/Dark
# Corresponds to winnative and xpnative built-in tkinter themes

# Because this library is now a class, we needs imports:
import re
import tkinter as tk
from tkinter import ttk


# Colors
###################


LIGHT_COLORS = {
    'clean': {
        'label_bg': "#e1e1e1",
        'hover_bg': "#c7e0f4",
        'click_bg': "#a9d1f5",
        'border_color': "#adadad",
        'hover_border': "#0078d7",
        'click_border': "#005499",
        'text_bg': "#ffffff",
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
        'text_bg': "#ffffff",
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
        'text_bg': "#181818",
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
        'text_bg': "#181818",
        'text_color': "#ffffff",
        'labelframe_bg': "#505050",
        'labelframe_fg': "#ffffff"
    }
}






##################################
#                                #
#   FANCYBUTTUON STYLE LIBRARY   #
#                                #
##################################

class FancyButtonStyleLibrary:
    def __init__(self):
        self.style=ttk.Style()
        print(f"FancyButton initialized with FancyButtonStyleLibrary from {self.style_library.__class__.__module__}")
        # pass # Lol.

    # Use this to capture the _font## suffix and apply a font size
    # def get_font_size(self, widget):
    #     name = widget.winfo_name()
    #     font_match = re.search(r'font(\d+)', name)
    #     return int(font_match.group(1)) if font_match else 10  # default font size

    def get_font_size(self, widget):
        name = widget.winfo_name()
        font_match = re.search(r'font(\d+)', name)
        size = int(font_match.group(1)) if font_match else 10
        print(f"Widget: {name}, Font size: {size}")  # Debug print
        return size


# Main styling function
##############################


    # def style_widget(self, widget, bg_color, fg_color, theme, mode):
    #     if isinstance(widget, tk.Widget):
    #         self.style_tk_widget(widget, bg_color, fg_color, theme, mode)
    #     elif isinstance(widget, ttk.Widget):
    #         self.style_ttk_widget(widget, bg_color, fg_color, theme, mode)




    # def style_widget(self, widget, bg_color, fg_color, theme, mode):
    #     font_size = self.get_font_size(widget)
    #     widget_class = widget.winfo_class()
        
    #     if isinstance(widget, (tk.Label, tk.Button, tk.Entry, tk.Text, tk.Listbox)):
    #         widget.configure(
    #             background=bg_color,
    #             foreground=fg_color,
    #             font=("TkDefaultFont", font_size)
    #         )
    #     elif isinstance(widget, ttk.Widget):
    #         style_name = f"{widget}.{widget_class}"
    #         if widget_class in ['TFrame', 'TLabel', 'TButton', 'TRadiobutton', 'TCheckbutton']: # , 'TEntry', 'TCombobox'
    #             self.style.configure(style_name, 
    #                 background=bg_color, 
    #                 foreground=fg_color, 
    #                 font=("TkDefaultFont", font_size)
    #             )
    #             widget.configure(style=style_name)
    #         elif widget_class == 'TFrame':
    #             self.style.configure(style_name, background=bg_color)
    #         elif widget_class == 'TSeparator':
    #             self.style.configure(style_name, background=bg_color)
        
    #     print(f"Styled {widget_class}: {widget}, font size: {font_size}")




    # def style_widget(self, widget, bg_color, fg_color, theme, mode):
    #     font_size = self.get_font_size(widget)
    #     widget_class = widget.winfo_class()
        
    #     if isinstance(widget, tk.Listbox):
    #         widget.configure(
    #             background=bg_color,
    #             foreground=fg_color,
    #             font=("TkDefaultFont", font_size),
    #             selectbackground=LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'],
    #             selectforeground=fg_color
    #         )
    #     elif isinstance(widget, (tk.Label, tk.Button, tk.Entry, tk.Text)):
    #         widget.configure(
    #             background=bg_color,
    #             foreground=fg_color,
    #             font=("TkDefaultFont", font_size)
    #         )
    #     elif isinstance(widget, ttk.Widget):
    #         style_name = f"{widget}.{widget_class}"
    #         if widget_class in ['TLabel', 'TButton', 'TEntry', 'TCombobox', 'TRadiobutton']:
    #             self.style.configure(style_name, 
    #                 background=bg_color, 
    #                 foreground=fg_color, 
    #                 font=("TkDefaultFont", font_size)
    #             )
    #             if widget_class == 'TRadiobutton':
    #                 self.style.map(style_name,
    #                     background=[('active', LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'])],
    #                     foreground=[('active', fg_color)]
    #                 )
    #             widget.configure(style=style_name)
    #         elif widget_class == 'TFrame':
    #             self.style.configure(style_name, 
    #                 background=bg_color,
    #                 relief='flat',
    #                 borderwidth=0
    #             )
    #         elif widget_class == 'TSeparator':
    #             self.style.configure(style_name, background=bg_color)
        
    #     print(f"Styled {widget_class}: {widget}, font size: {font_size}")

    def style_widget(self, widget, theme, mode, state):
        print(f"FancyButtonStyleLibrary.style_widget called with: widget={widget}, theme={theme}, mode={mode}, state={state}")

        print(f"Entering style_widget with args: {args}")
        if len(args) < 4:
            print(f"Error: Not enough arguments. Expected 4, got {len(args)}")
            return
        widget, theme, mode, state = args[:4]
        widget_class = widget.winfo_class()
        colors = self.get_colors(theme, mode)
        font_size = self.get_font_size(widget)
        
        if isinstance(widget, tk.Listbox):
            self.style_tk_listbox(widget, bg_color, fg_color, theme, mode)
        elif isinstance(widget, (tk.Label, tk.Button, tk.Entry, tk.Text)):
            widget.configure(
                background=bg_color,
                foreground=fg_color,
                font=("TkDefaultFont", font_size)
            )
        elif isinstance(widget, ttk.Widget):
            style_name = f"{widget}.{widget_class}"
            if widget_class == 'TFrame':
                self.style_ttk_frame(widget, bg_color, theme, mode)
            elif widget_class in ['TLabel', 'TButton', 'TEntry', 'TCombobox', 'TCheckbutton', 'TRadiobutton']:
                self.style.configure(style_name, 
                    background=bg_color, 
                    foreground=fg_color, 
                    font=("TkDefaultFont", font_size)
                )
                if widget_class == ['TRadiobutton']:
                    self.style.map(style_name,
                        background=[('active', LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'])],
                        foreground=[('active', fg_color)]
                    )
                widget.configure(style=style_name)
            elif widget_class == 'TSeparator':
                self.style.configure(style_name, background=bg_color)
        
        print(f"Styled {widget_class}: {widget}, font size: {font_size}")


    def style_tk_widget(self, widget, bg_color, fg_color, theme, mode):
        widget_type = widget.winfo_class()
        font_size = self.get_font_size(widget)
        

        # For fonts
        if widget_type in ['Label', 'Button', 'Entry', 'Text']:
            widget.configure(
                background=bg_color,
                foreground=fg_color,
                font=("TkDefaultFont", font_size)
            )
        
        # Tk widgets
        if widget_type == "Label":
            self.style_tk_label(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "Button":
            self.style_tk_button(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "Entry":
            self.style_tk_entry(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "Text":
            self.style_tk_text(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "Frame":
            self.style_tk_frame(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "LabelFrame":
            self.style_tk_labelframe(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "PanedWindow":
            self.style_tk_panedwindow(widget, bg_color, theme, mode)
        elif widget_type == "Scrollbar":
            self.style_tk_scrollbar(widget, bg_color, theme, mode)
        elif widget_type == "Canvas":
            self.style_tk_canvas(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "Listbox":
            self.style_tk_listbox(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "Scale":
            self.style_tk_scale(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "Spinbox":
            self.style_tk_spinbox(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "Menubutton":
            self.style_tk_menubutton(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "Menu":
            self.style_tk_menu(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "Radiobutton":
            self.style_tk_radiobutton(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "Checkbutton":
            self.style_tk_checkbutton(widget, bg_color, fg_color, theme, mode)



    def style_ttk_widget(self, widget, bg_color, fg_color, theme, mode):
        widget_type = widget.winfo_class()
        font_size = self.get_font_size(widget)
        
        # For fonts
        if widget_type in ['TLabel', 'TButton', 'TEntry']:
            widget.configure(
                background=bg_color,
                foreground=fg_color,
                font=("TkDefaultFont", font_size)
            )

        # Ttk widgets
        elif widget_type == "TButton":
            self.style_ttk_button(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "TCheckbutton":
            self.style_ttk_checkbutton(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "TCombobox":
            self.style_ttk_combobox(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "TEntry":
            self.style_ttk_entry(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "TFrame":
            self.style_ttk_frame(widget, bg_color, theme, mode)
        elif widget_type == "TLabel":
            self.style_ttk_label(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "TLabelframe":
            self.style_ttk_labelframe(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "TMenubutton":
            self.style_ttk_menubutton(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "TNotebook":
            self.style_ttk_notebook(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "TPanedwindow":
            self.style_ttk_panedwindow(widget, bg_color, theme, mode)
        elif widget_type == "Progressbar":
            self.style_ttk_progressbar(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "TRadiobutton":
            self.style_ttk_radiobutton(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "TScale":
            self.style_ttk_scale(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "TScrollbar":
            self.style_ttk_scrollbar(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "TSeparator":
            self.style_ttk_separator(widget, bg_color, theme, mode)
        elif widget_type == "TSizegrip":
            self.style_ttk_sizegrip(widget, bg_color, theme, mode)
        elif widget_type == "TSpinbox":
            self.style_ttk_spinbox(widget, bg_color, fg_color, theme, mode)
        elif widget_type == "Treeview":
            self.style_ttk_treeview(widget, bg_color, fg_color, theme, mode)
        

        


# Tk Widgets
###########################

    def style_tk_label(self, widget, bg_color, fg_color, theme, mode):
        widget.configure(
            background=bg_color,
            foreground=fg_color,
            font=("", self.get_font_size(widget)),
            borderwidth=1,
            relief="flat",
            padx=1,
            pady=1,
            anchor="center",
            justify="left",
            wraplength=0,
            underline=-1,
            width=0,
            height=0,
            cursor="",
            text=widget.cget("text"),
            image=None,
            compound="none",
            highlightbackground=bg_color,
            highlightcolor=fg_color,
            highlightthickness=0,
            takefocus=0
        )

    def style_tk_button(self, widget, bg_color, fg_color, theme, mode):
        widget.configure(
            background=bg_color,
            foreground=fg_color,
            activebackground=LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'],
            activeforeground=fg_color,
            disabledforeground='gray',
            font=("TkDefaultFont", self.get_font_size(widget)),
            borderwidth=2 if theme == 'retro' else 1,
            relief="raised" if theme == 'retro' else "flat",
            padx=1,
            pady=1,
            anchor="center",
            justify="center",
            wraplength=0,
            underline=-1,
            width=0,
            height=0,
            cursor="",
            text=widget.cget("text"),
            image=None,
            compound="none",
            highlightbackground=bg_color,
            highlightcolor=fg_color,
            highlightthickness=0,
            takefocus=1,
            command=widget.cget("command"),
            default="normal",
            overrelief="raised",
            state="normal"
        )

    def style_tk_entry(self, widget, bg_color, fg_color, theme, mode):
        widget.configure(
            background=bg_color,
            foreground=fg_color,
            insertbackground=fg_color,
            selectbackground=LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'],
            selectforeground=fg_color,
            disabledbackground='gray',
            disabledforeground='gray',
            font=("TkDefaultFont", self.get_font_size(widget)),
            borderwidth=2 if theme == 'retro' else 1,
            relief="sunken",
            justify="left",
            cursor="xterm",
            highlightbackground=bg_color,
            highlightcolor=fg_color,
            highlightthickness=0,
            insertborderwidth=0,
            insertofftime=300,
            insertontime=600,
            insertwidth=2,
            readonlybackground='gray',
            show="",
            state="normal",
            takefocus=1,
            textvariable=None,
            validate="none",
            validatecommand=None,
            width=20,
            xscrollcommand=None
        )

    def style_tk_text(self, widget, bg_color, fg_color, theme, mode):
        widget.configure(
            background=bg_color,
            foreground=fg_color,
            insertbackground=fg_color,
            selectbackground=LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'],
            selectforeground=fg_color,
            font=("TkDefaultFont", self.get_font_size(widget)),
            borderwidth=2 if theme == 'retro' else 1,
            relief="sunken",
            cursor="xterm",
            highlightbackground=bg_color,
            highlightcolor=fg_color,
            highlightthickness=0,
            insertborderwidth=0,
            insertofftime=300,
            insertontime=600,
            insertwidth=2,
            padx=1,
            pady=1,
            setgrid=0,
            spacing1=0,
            spacing2=0,
            spacing3=0,
            state="normal",
            tabs=(),
            takefocus=1,
            wrap="char",
            xscrollcommand=None,
            yscrollcommand=None
        )

    def style_tk_frame(self, widget, bg_color, fg_color, theme, mode):
        widget.configure(
            background=bg_color,
            borderwidth=0,
            relief="flat",
            cursor="",
            highlightbackground=bg_color,
            highlightcolor=fg_color,
            highlightthickness=0,
            padx=0,
            pady=0,
            takefocus=0
        )

    def style_tk_labelframe(self, widget, bg_color, fg_color, theme, mode):
        widget.configure(
            background=bg_color,
            foreground=fg_color,
            font=("TkDefaultFont", self.get_font_size(widget)),
            borderwidth=2,
            relief="groove",
            cursor="",
            highlightbackground=bg_color,
            highlightcolor=fg_color,
            highlightthickness=0,
            padx=0,
            pady=0,
            takefocus=0,
            text=widget.cget("text"),
            labelanchor="nw",
            labelwidget=None
        )

    def style_tk_panedwindow(self, widget, bg_color, theme, mode):
        widget.configure(
            background=bg_color,
            borderwidth=2,
            relief="flat",
            cursor="",
            handlepad=8,
            handlesize=8,
            opaqueresize=1,
            orient="horizontal",
            proxybackground=bg_color,
            proxyborderwidth=2,
            proxyrelief="raised",
            sashcursor="",
            sashpad=0,
            sashrelief="flat",
            sashwidth=3,
            showhandle=0
        )

    def style_tk_scrollbar(self, widget, bg_color, theme, mode):
        widget.configure(
            activebackground=LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'],
            activerelief="raised",
            background=bg_color,
            borderwidth=2,
            cursor="arrow",
            elementborderwidth=1,
            highlightbackground=bg_color,
            highlightcolor=fg_color,
            highlightthickness=0,
            jump=0,
            orient="vertical",
            relief="sunken",
            repeatdelay=300,
            repeatinterval=100,
            takefocus=0,
            troughcolor=bg_color,
            width=16
        )

    def style_tk_canvas(self, widget, bg_color, fg_color, theme, mode):
        widget.configure(
            background=bg_color,
            borderwidth=0,
            closeenough=1.0,
            confine=1,
            cursor="",
            highlightbackground=bg_color,
            highlightcolor=fg_color,
            highlightthickness=0,
            insertbackground=fg_color,
            insertborderwidth=0,
            insertofftime=300,
            insertontime=600,
            insertwidth=2,
            offset="0,0",
            relief="flat",
            scrollregion=(),
            selectbackground=LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'],
            selectborderwidth=1,
            selectforeground=fg_color,
            state="normal",
            takefocus=0,
            xscrollcommand=None,
            xscrollincrement=0,
            yscrollcommand=None,
            yscrollincrement=0
        )

    def style_tk_listbox(self, widget, bg_color, fg_color, theme, mode):
        widget.configure(
            background="#ff0000", # colors['text_bg'],
            foreground=colors['text_color'],
            font=("TkDefaultFont", self.get_font_size(widget)),
            borderwidth=2 if theme == 'retro' else 1,
            relief="sunken",
            cursor="",
            exportselection=1,
            highlightbackground=bg_color,
            highlightcolor=fg_color,
            highlightthickness=0,
            selectbackground=LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'],
            selectborderwidth=1,
            selectforeground=fg_color,
            selectmode="browse",
            setgrid=0,
            state="normal",
            takefocus=1,
            xscrollcommand=None,
            yscrollcommand=None,
            listvariable=None
        )

    def style_tk_scale(self, widget, bg_color, fg_color, theme, mode):
        widget.configure(
            activebackground=LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'],
            background=bg_color,
            bigincrement=0,
            borderwidth=2,
            cursor="",
            digits=0,
            font=("TkDefaultFont", self.get_font_size(widget)),
            foreground=fg_color,
            from_=0,
            highlightbackground=bg_color,
            highlightcolor=fg_color,
            highlightthickness=0,
            label="",
            length=100,
            orient="horizontal",
            relief="flat",
            repeatdelay=300,
            repeatinterval=100,
            resolution=1,
            showvalue=1,
            sliderlength=30,
            sliderrelief="raised",
            state="normal",
            takefocus=1,
            tickinterval=0,
            to=100,
            troughcolor=bg_color,
            variable=None,
            width=15
        )

    def style_tk_spinbox(self, widget, bg_color, fg_color, theme, mode):
        widget.configure(
            activebackground=LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'],
            background=bg_color,
            borderwidth=2 if theme == 'retro' else 1,
            buttonbackground=bg_color,
            buttoncursor="arrow",
            buttondownrelief="raised",
            buttonuprelief="raised",
            command=None,
            cursor="xterm",
            disabledbackground='gray',
            disabledforeground='gray',
            exportselection=1,
            font=("TkDefaultFont", self.get_font_size(widget)),
            foreground=fg_color,
            format="%s",
            from_=0,
            highlightbackground=bg_color,
            highlightcolor=fg_color,
            highlightthickness=0,
            increment=1,
            insertbackground=fg_color,
            insertborderwidth=0,
            insertofftime=300,
            insertontime=600,
            insertwidth=2,
            justify="left",
            relief="sunken",
            readonlybackground='gray',
            repeatdelay=400,
            repeatinterval=100,
            selectbackground=LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'],
            selectborderwidth=1,
            selectforeground=fg_color,
            state="normal",
            takefocus=1,
            textvariable=None,
            to=100,
            validate="none",
            validatecommand=None,
            values=(),
            width=20,
            wrap=0,
            xscrollcommand=None
        )

    def style_tk_menubutton(self, widget, bg_color, fg_color, theme, mode):
        widget.configure(
            activebackground=LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'],
            activeforeground=fg_color,
            anchor="center",
            background=bg_color,
            bitmap="",
            borderwidth=2 if theme == 'retro' else 1,
            cursor="",
            direction="below",
            disabledforeground='gray',
            font=("TkDefaultFont", self.get_font_size(widget)),
            foreground=fg_color,
            height=0,
            highlightbackground=bg_color,
            highlightcolor=fg_color,
            highlightthickness=0,
            image=None,
            indicatoron=1,
            justify="center",
            menu=None,
            padx=1,
            pady=1,
            relief="raised",
            compound="none",
            state="normal",
            takefocus=0,
            text=widget.cget("text"),
            textvariable=None,
            underline=-1,
            width=0,
            wraplength=0
        )

    def style_tk_menu(self, widget, bg_color, fg_color, theme, mode):
        widget.configure(
            activebackground=LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'],
            activeforeground=fg_color,
            activeborderwidth=1,
            background=bg_color,
            borderwidth=1,
            cursor="arrow",
            disabledforeground='gray',
            font=("TkDefaultFont", self.get_font_size(widget)),
            foreground=fg_color,
            postcommand=None,
            relief="raised",
            selectcolor=fg_color,
            takefocus=0,
            tearoff=1,
            tearoffcommand=None,
            title="",
            type="normal"
        )

    def style_tk_radiobutton(self, widget, bg_color, fg_color, theme, mode):
        widget.configure(
            activebackground=LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'],
            activeforeground=fg_color,
            anchor="center",
            background=bg_color,
            bitmap="",
            borderwidth=2 if theme == 'retro' else 1,
            command=widget.cget("command"),
            compound="none",
            cursor="",
            disabledforeground='gray',
            font=("TkDefaultFont", self.get_font_size(widget)),
            foreground=fg_color,
            height=0,
            highlightbackground=bg_color,
            highlightcolor=fg_color,
            highlightthickness=0,
            image=None,
            indicatoron=1,
            justify="center",
            offrelief="raised",
            overrelief="raised",
            padx=1,
            pady=1,
            relief="flat",
            selectcolor=fg_color,
            state="normal",
            takefocus=1,
            text=widget.cget("text"),
            textvariable=None,
            underline=-1,
            value=None,
            variable=None,
            width=0,
            wraplength=0
        )

    def style_tk_checkbutton(self, widget, bg_color, fg_color, theme, mode):
        widget.configure(
            activebackground=LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'],
            activeforeground=fg_color,
            anchor="center",
            background=bg_color,
            bitmap="",
            borderwidth=2 if theme == 'retro' else 1,
            command=widget.cget("command"),
            compound="none",
            cursor="",
            disabledforeground='gray',
            font=("TkDefaultFont", self.get_font_size(widget)),
            foreground=fg_color,
            height=0,
            highlightbackground=bg_color,
            highlightcolor=fg_color,
            highlightthickness=0,
            image=None,
            indicatoron=1,
            justify="center",
            offrelief="raised",
            onrelief="raised",
            overrelief="raised",
            padx=1,
            pady=1,
            relief="flat",
            selectcolor=fg_color,
            selectimage=None,
            state="normal",
            takefocus=1,
            text=widget.cget("text"),
            textvariable=None,
            underline=-1,
            variable=None,
            width=0,
            wraplength=0
        )






# Ttk Widgets
################################

    def style_ttk_button(self, widget, bg_color, fg_color, theme, mode):
        style_name = f"{widget}.TButton"
        self.style.configure(style_name,
            background=bg_color,
            foreground=fg_color,
            relief="raised" if theme == 'retro' else "flat",
            borderwidth=2 if theme == 'retro' else 1,
            font=("TkDefaultFont", self.get_font_size(widget)),
            padding=(1, 1),
            anchor="center",
            justify="center",
            width=-1,
            compound="none"
        )
        self.style.map(style_name,
            background=[('active', LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'])],
            foreground=[('active', fg_color)],
            relief=[('pressed', 'sunken'), ('!pressed', 'raised' if theme == 'retro' else 'flat')]
        )
        widget.configure(style=style_name)

    def style_ttk_checkbutton(self, widget, bg_color, fg_color, theme, mode):
        style_name = f"{widget}.TCheckbutton"
        self.style.configure(style_name,
            background=bg_color,
            foreground=fg_color,
            font=("TkDefaultFont", self.get_font_size(widget)),
            relief="flat",
            borderwidth=0,
            padding=(1, 1),
            anchor="center",
            justify="left",
            width=-1,
            compound="none",
            indicatorcolor=fg_color,
            indicatorrelief="sunken" if theme == 'retro' else "flat"
        )
        self.style.map(style_name,
            background=[('active', LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'])],
            foreground=[('active', fg_color)],
            indicatorcolor=[('selected', LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'])]
        )
        widget.configure(style=style_name)

    def style_ttk_combobox(self, widget, bg_color, fg_color, theme, mode):
        style_name = f"{widget}.TCombobox"
        self.style.configure(style_name,
            background=bg_color,
            foreground=fg_color,
            fieldbackground=bg_color,
            font=("TkDefaultFont", self.get_font_size(widget)),
            relief="sunken",
            borderwidth=2 if theme == 'retro' else 1,
            padding=(1, 1),
            arrowcolor=fg_color,
            arrowsize=12
        )
        self.style.map(style_name,
            background=[('active', LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'])],
            foreground=[('active', fg_color)],
            fieldbackground=[('readonly', bg_color)],
            selectbackground=[('focus', LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'])],
            selectforeground=[('focus', fg_color)]
        )
        widget.configure(style=style_name)

    def style_ttk_entry(self, widget, bg_color, fg_color, theme, mode):
        style_name = f"{widget}.TEntry"
        self.style.configure(style_name,
            background=bg_color,
            foreground=fg_color,
            fieldbackground=bg_color,
            font=("TkDefaultFont", self.get_font_size(widget)),
            relief="sunken",
            borderwidth=2 if theme == 'retro' else 1,
            padding=(1, 1),
            insertcolor=fg_color,
            insertwidth=2
        )
        self.style.map(style_name,
            background=[('active', LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'])],
            foreground=[('active', fg_color)],
            fieldbackground=[('readonly', bg_color)],
            selectbackground=[('focus', LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'])],
            selectforeground=[('focus', fg_color)]
        )
        widget.configure(style=style_name)

    def style_ttk_frame(self, widget, bg_color, theme, mode):
        style_name = f"{widget}.TFrame"
        hover_bg = LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg']
        click_bg = LIGHT_COLORS[theme]['click_bg'] if mode == "light" else DARK_COLORS[theme]['click_bg']
        
        self.style.configure(style_name,
            background=bg_color,
            relief="flat",
            borderwidth=0
        )
        
        self.style.map(style_name,
            background=[
                ('active', hover_bg),
                ('pressed', click_bg)
            ],
            relief=[
                ('active', 'raised'),
                ('pressed', 'sunken')
            ]
        )
        
        widget.configure(style=style_name)

    def style_ttk_label(self, widget, bg_color, fg_color, theme, mode):
        style_name = f"{widget}.TLabel"
        self.style.configure(style_name,
            background=bg_color,
            foreground=fg_color,
            font=("TkDefaultFont", self.get_font_size(widget)),
            relief="flat",
            borderwidth=0,
            padding=(1, 1),
            anchor="center",
            justify="left",
            width=-1,
            compound="none"
        )
        widget.configure(style=style_name)

    def style_ttk_labelframe(self, widget, bg_color, fg_color, theme, mode):
        style_name = f"{widget}.TLabelframe"
        self.style.configure(style_name,
            background=bg_color,
            foreground=fg_color,
            font=("TkDefaultFont", self.get_font_size(widget)),
            relief="groove",
            borderwidth=2,
            padding=(1, 1),
            labelmargins=(2, 2),
            labeloutside=False
        )
        self.style.configure(f"{style_name}.Label",
            background=bg_color,
            foreground=fg_color,
            font=("TkDefaultFont", self.get_font_size(widget))
        )
        widget.configure(style=style_name)

    def style_ttk_menubutton(self, widget, bg_color, fg_color, theme, mode):
        style_name = f"{widget}.TMenubutton"
        self.style.configure(style_name,
            background=bg_color,
            foreground=fg_color,
            relief="raised" if theme == 'retro' else "flat",
            borderwidth=2 if theme == 'retro' else 1,
            font=("TkDefaultFont", self.get_font_size(widget)),
            padding=(1, 1),
            anchor="center",
            justify="center",
            width=-1,
            compound="none",
            arrowcolor=fg_color,
            arrowsize=12
        )
        self.style.map(style_name,
            background=[('active', LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'])],
            foreground=[('active', fg_color)],
            relief=[('pressed', 'sunken'), ('!pressed', 'raised' if theme == 'retro' else 'flat')]
        )
        widget.configure(style=style_name)

    def style_ttk_notebook(self, widget, bg_color, fg_color, theme, mode):
        style_name = f"{widget}.TNotebook"
        self.style.configure(style_name,
            background=bg_color,
            foreground=fg_color,
            relief="flat",
            borderwidth=0,
            tabmargins=(2, 2, 2, 0),
            tabposition="nw"
        )
        self.style.configure(f"{style_name}.Tab",
            background=bg_color,
            foreground=fg_color,
            font=("TkDefaultFont", self.get_font_size(widget)),
            relief="raised" if theme == 'retro' else "flat",
            borderwidth=2 if theme == 'retro' else 1,
            padding=(3, 1),
            compound="none"
        )
        self.style.map(f"{style_name}.Tab",
            background=[('selected', LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'])],
            foreground=[('selected', fg_color)],
            expand=[('selected', (1, 1, 1, 0))]
        )
        widget.configure(style=style_name)

    def style_ttk_panedwindow(self, widget, bg_color, theme, mode):
        style_name = f"{widget}.TPanedwindow"
        self.style.configure(style_name,
            background=bg_color,
            relief="flat",
            borderwidth=0,
            sashrelief="raised",
            sashwidth=3,
            sashpad=0,
            handlepad=8,
            handlesize=8,
            opaqueresize=True
        )
        widget.configure(style=style_name)

    def style_ttk_progressbar(self, widget, bg_color, fg_color, theme, mode):
        style_name = f"{widget}.TProgressbar"
        self.style.configure(style_name,
            background=LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'],
            foreground=fg_color,
            troughcolor=bg_color,
            borderwidth=2 if theme == 'retro' else 1,
            relief="sunken",
            thickness=20
        )
        widget.configure(style=style_name)

    def style_ttk_radiobutton(self, widget, bg_color, fg_color, theme, mode):
        style_name = f"{widget}.TRadiobutton"
        self.style.configure(style_name,
            background=bg_color,
            foreground=fg_color,
            font=("TkDefaultFont", self.get_font_size(widget)),
            relief="flat",
            borderwidth=0,
            padding=(1, 1),
            anchor="center",
            justify="left",
            width=-1,
            compound="none",
            indicatorcolor=fg_color,
            indicatorrelief="sunken" if theme == 'retro' else "flat"
        )
        self.style.map(style_name,
            background=[('active', LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'])],
            foreground=[('active', fg_color)],
            indicatorcolor=[('selected', LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'])]
        )
        widget.configure(style=style_name)

    def style_ttk_scale(self, widget, bg_color, fg_color, theme, mode):
        style_name = f"{widget}.TScale"
        self.style.configure(style_name,
            background=bg_color,
            foreground=fg_color,
            troughcolor=bg_color,
            sliderrelief="raised",
            sliderlength=30,
            sliderthickness=20,
            borderwidth=2 if theme == 'retro' else 1,
            relief="flat"
        )
        self.style.map(style_name,
            background=[('active', LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'])]
        )
        widget.configure(style=style_name)

    def style_ttk_scrollbar(self, widget, bg_color, fg_color, theme, mode):
        style_name = f"{widget}.TScrollbar"
        self.style.configure(style_name,
            background=bg_color,
            troughcolor=bg_color,
            bordercolor=fg_color,
            arrowcolor=fg_color,
            relief="flat",
            borderwidth=0,
            arrowsize=13,
            width=16
        )
        self.style.map(style_name,
            background=[('active', LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'])]
        )
        widget.configure(style=style_name)

    def style_ttk_separator(self, widget, bg_color, theme, mode):
        style_name = f"{widget}.TSeparator"
        self.style.configure(style_name,
            background=bg_color,
            relief="sunken",
            borderwidth=1
        )
        widget.configure(style=style_name)

    def style_ttk_sizegrip(self, widget, bg_color, theme, mode):
        style_name = f"{widget}.TSizegrip"
        self.style.configure(style_name,
            background=bg_color
        )
        widget.configure(style=style_name)

    def style_ttk_spinbox(self, widget, bg_color, fg_color, theme, mode):
        style_name = f"{widget}.TSpinbox"
        self.style.configure(style_name,
            background=bg_color,
            foreground=fg_color,
            fieldbackground=bg_color,
            font=("TkDefaultFont", self.get_font_size(widget)),
            arrowcolor=fg_color,
            relief="sunken",
            borderwidth=2 if theme == 'retro' else 1,
            padding=(1, 1),
            arrowsize=12
        )
        self.style.map(style_name,
            background=[('active', LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'])],
            foreground=[('active', fg_color)],
            fieldbackground=[('readonly', bg_color)],
            selectbackground=[('focus', LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'])],
            selectforeground=[('focus', fg_color)]
        )
        widget.configure(style=style_name)

    def style_ttk_treeview(self, widget, bg_color, fg_color, theme, mode):
        style_name = f"{widget}.Treeview"
        self.style.configure(style_name,
            background=bg_color,
            foreground=fg_color,
            fieldbackground=bg_color,
            font=("TkDefaultFont", self.get_font_size(widget)),
            relief="sunken",
            borderwidth=2 if theme == 'retro' else 1,
            rowheight=20
        )
        self.style.map(style_name,
            background=[('selected', LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'])],
            foreground=[('selected', fg_color)]
        )
        self.style.configure(f"{style_name}.Heading",
            background=bg_color,
            foreground=fg_color,
            font=("TkDefaultFont", self.get_font_size(widget), "bold"),
            relief="raised",
            borderwidth=1
        )
        self.style.map(f"{style_name}.Heading",
            background=[('active', LIGHT_COLORS[theme]['hover_bg'] if mode == "light" else DARK_COLORS[theme]['hover_bg'])],
            foreground=[('active', fg_color)]
        )
        widget.configure(style=style_name)








