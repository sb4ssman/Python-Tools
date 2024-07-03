# -*- coding: utf-8 -*-
"""
Created on Sat Jun 6 10:14:14 2024

@author: Thomas
"""



"""
ToolTip Class for Tkinter
-------------------------

This module provides a customizable ToolTip class for Tkinter applications.
It allows you to easily add tooltips to any Tkinter widget.

Features:
- Create tooltips for any Tkinter widget
- Enable/disable tooltips dynamically
- Update tooltip text on the fly
- Two methods of creation: simple and named instance

Usage:
1. Simple Creation:
   createToolTip(widget, "Tooltip text")
   
   This method automatically binds the tooltip to the widget and adds
   tooltip-specific methods to the widget.

2. Named Instance:
   tooltip = createNamedToolTip(widget, "Tooltip text")
   
   This method returns a ToolTip instance, allowing for more direct control.

Tooltip Management:
- For tooltips created with Method 1:
  widget.tt_get_text()  # Get current tooltip text
  widget.tt_set_text("New text")  # Update tooltip text
  widget.tt_enable()  # Enable tooltip
  widget.tt_disable()  # Disable tooltip

- For tooltips created with Method 2:
  tooltip.text  # Get current tooltip text
  tooltip.update_text("New text")  # Update tooltip text
  tooltip.enable()  # Enable tooltip
  tooltip.disable()  # Disable tooltip

Example:
  import tkinter as tk
  from tooltip import createToolTip, createNamedToolTip

  root = tk.Tk()

  # Method 1
  label1 = tk.Label(root, text="Hover me (Method 1)")
  label1.pack()
  createToolTip(label1, "This is a tooltip")

  # Method 2
  label2 = tk.Label(root, text="Hover me (Method 2)")
  label2.pack()
  tooltip2 = createNamedToolTip(label2, "This is another tooltip")

  root.mainloop()

Notes:
- The ToolTip class can be easily integrated into existing Tkinter applications.
- Tooltips are customizable in terms of appearance and behavior.
- The module includes a demo class (TooltipDemo) that showcases various tooltip functionalities.

For more detailed examples and advanced usage, refer to the TooltipDemo class in this file.
"""


##############################
#                            #
#   TOOLTIP CLASS TEMPLATE   #
#                            #
##############################

# Stuff this class into an app and you can make tooltips at your lesiure 


# STANDARD IMPORTS
###############################

import tkinter as tk


# ToolTip Class
###########################

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.enabled = True

    def showtip(self):
        "Display text in tooltip window"
        if not self.enabled or self.tipwindow or not self.text: # Confirm it's supposed to draw or break out
            return
        
        # Edit this to change how the tips look (maybe don't edit it after all)
        x, y, _, _ = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 25
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                      background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

    def update_text(self, new_text):
        self.text = new_text
        if self.tipwindow:
            label = self.tipwindow.winfo_children()[0]
            label.config(text=self.text)

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False
        self.hidetip()

    def remove(self):
        self.widget.unbind('<Enter>')
        self.widget.unbind('<Leave>')

def createToolTip(widget, text):
    toolTip = ToolTip(widget, text)
    def enter(event):
        try:
            toolTip.showtip()
        except:
            pass  # If showtip fails, we simply don't show the tooltip
    def leave(event):
        toolTip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)

    widget.tooltip = toolTip
    widget.tt_get_text = lambda: toolTip.text
    widget.tt_set_text = toolTip.update_text
    widget.tt_enable = toolTip.enable
    widget.tt_disable = toolTip.disable
    widget.tt_enabled = True


def createNamedToolTip(widget, text):
    tooltip = ToolTip(widget, text)
    widget.bind('<Enter>', lambda event: tooltip.showtip())
    widget.bind('<Leave>', lambda event: tooltip.hidetip())
    return tooltip



##########################################################
#   END TEMPLATE   #   END TEMPLATE   #   END TEMPLATE   #


# More notes:

# Have a thing:
# screenshot_checkbox = tk.Checkbutton(root, text="Take Screenshot")
# screenshot_checkbox.pack(side=tk.RIGHT, padx=5)

# Make a tooltip:
# createToolTip(screenshot_checkbox, "Capture the screen when clicking")

# self.screenshot_checkbox_tooltip.update_text("You can update the text of the tip!")

# self.screenshot_checkbox_tooltip.remove()

# Example App:
# observe unnecessary excuses to call examples of these tips. 

class TooltipDemo:
    def __init__(self, master):
        self.master = master
        master.geometry("400x300")
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