# -*- coding: utf-8 -*-
"""
Created on Sun Jun 7 17:37:45 2024

@author: Thomas
"""



# Have a thing:
# screenshot_checkbox = tk.Checkbutton(root, text="Take Screenshot")
# screenshot_checkbox.pack(side=tk.RIGHT, padx=5)

# Make a tooltip:
# createToolTip(screenshot_checkbox, "Capture the screen when clicking")

# self.screenshot_checkbox_tooltip.update_text("You can update the text of the tip!")

# self.screenshot_checkbox_tooltip.remove()

# Example App:
# observe unnecessary excuses to call examples of these tips. 






# import tkinter as tk
# from python_tools.utils.ToolTips import createToolTip, createNamedToolTip


import tkinter as tk

import sys
import os


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# print("Python version:", sys.version)
# print("Current working directory:", os.getcwd())
# print("Python path:", sys.path)

# try:
#     print("nothing")
#     #from utils.ToolTips import createToolTip, createNamedToolTip
# except ImportError as e:
#     print(f"Failed to import from utils.ToolTips: {e}")
#     print("Contents of current directory:", os.listdir())
#     print("Contents of utils directory:", os.listdir("utils"))
    
#     # Try absolute import
#     try:
#         # from python_tools.utils.ToolTips import createToolTip, createNamedToolTip
#         print("Successfully imported using absolute import")
#     except ImportError as e:
#         print(f"Failed to import using absolute import: {e}")

from utils.ToolTips import createToolTip, createNamedToolTip


class TooltipDemo:
    def __init__(self, master):
        self.master = master
        master.geometry("350x250")
        master.title("Tooltip Demo")

        # Method 1: Using createToolTip (original method)
        self.label1 = tk.Label(master, text="Hover here (Method 1)")
        self.label1.grid(row=0, column=0, pady=10, padx=10)
        createToolTip(self.label1, "This tooltip was created using createToolTip") # The easy straightforward way

        # Method 2: Creating a named ToolTip instance
        self.label2 = tk.Label(master, text="Hover here (Method 2)")
        self.label2.grid(row=0, column=1, pady=10, padx=10)
        self.tooltip2 = createNamedToolTip(self.label2, "This tooltip was created as a named instance") # instantiate on a named var: control over binding - default is same as other method


        # Buttons for demonstrating tooltip management
        tk.Button(master, text="Update Method 1", command=self.update_tooltip1).grid(row=1, column=0, pady=5)
        tk.Button(master, text="Update Method 2", command=self.update_tooltip2).grid(row=1, column=1, pady=5)
        
        # Create and store toggle buttons as attributes
        self.toggle_button1 = tk.Button(master, text="Toggle Tip 1 Active", command=self.toggle_tooltip1)
        self.toggle_button1.grid(row=2, column=0, pady=5)
        self.toggle_button2 = tk.Button(master, text="Toggle Tip 2 Active", command=self.toggle_tooltip2)
        self.toggle_button2.grid(row=2, column=1, pady=5)

        # Print buttons, because you can get the text of the tips if you want
        tk.Button(master, text="Get Tip 1", command=self.get_tip1).grid(row=3, column=0, pady=5)
        tk.Button(master, text="Get Tip 2", command=self.get_tip2).grid(row=3, column=1, pady=5)

    def show_tooltip2(self, event):
        self.tooltip2.showtip()

    def hide_tooltip2(self, event):
        self.tooltip2.hidetip()

    def update_tooltip1(self):
        current_text = self.label1.tt_get_text()
        new_text = "Updated tooltip for Method 1" if current_text != "Updated tooltip for Method 1" else "This tooltip was created using createToolTip"
        self.label1.tt_set_text(new_text) # Method 1: .tt_set_text on the parent

    def update_tooltip2(self):
        current_text = self.tooltip2.text
        new_text = "Updated tooltip for Method 2" if current_text != "Updated tooltip for Method 2" else "This tooltip was created as a named instance"
        self.tooltip2.update_text(new_text)  # For Method 2, we can use the update_text method of our ToolTip instance

    def toggle_tooltip1(self):
        if self.label1.tt_enabled:
            self.label1.tt_disable()
            self.toggle_button1.config(text="Enable Tip 1")
        else:
            self.label1.tt_enable()
            self.toggle_button1.config(text="Disable Tip 1")
        self.label1.tt_enabled = not self.label1.tt_enabled

    def toggle_tooltip2(self):
        if self.tooltip2.enabled:
            self.tooltip2.disable()
            self.toggle_button2.config(text="Enable Tip 2")
        else:
            self.tooltip2.enable()
            self.toggle_button2.config(text="Disable Tip 2")

    def get_tip1(self):
        print("Tip 1:", self.label1.tt_get_text())

    def get_tip2(self):
        print("Tip 2:", self.tooltip2.text)

if __name__ == "__main__":
    root = tk.Tk()
    app = TooltipDemo(root)
    root.mainloop()