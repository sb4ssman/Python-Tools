# -*- coding: utf-8 -*-
"""
Created on Sat Jul 6 13:08:24 2024

@author: Thomas
"""

# This makes a custom itty bitty checkbutton

import tkinter as tk

# Tiny checkbox class
#########################

class TinyCheckbox(tk.Frame):
    def __init__(self, parent, text, variable, command=None):
        super().__init__(parent)
        self.variable = variable
        self.command = command

        # Create a tiny checkbox using Canvas
        self.checkbox = tk.Canvas(self, width=10, height=10, highlightthickness=0)
        self.checkbox.pack(side=tk.LEFT)
        self.box = self.checkbox.create_rectangle(2, 2, 8, 8, outline='black')
        self.check = self.checkbox.create_line(2, 5, 4, 7, 7, 3, fill='black', state='hidden')

        # Create a tiny label
        self.label = tk.Label(self, text=text, font=('TkDefaultFont', 6))
        self.label.pack(side=tk.LEFT)

        # Bind events
        self.checkbox.bind('<Button-1>', self.toggle)
        self.label.bind('<Button-1>', self.toggle)

        # Initial state
        self.update_state()

    def toggle(self, event=None):
        self.variable.set(not self.variable.get())
        self.update_state()
        if self.command:
            self.command()

    def update_state(self):
        if self.variable.get():
            self.checkbox.itemconfigure(self.check, state='normal')
        else:
            self.checkbox.itemconfigure(self.check, state='hidden')