# -*- coding: utf-8 -*-
"""
Created on Sat Jun 6 10:14:14 2024

@author: Thomas
"""


##############################
#                            #
#   TOOLTIP CLASS TEMPLATE   #
#                            #
##############################

# Stuff this class into an app and you can make tooltips at your lesiure 


# STANDARD IMPORTS
###############################









# ToolTip Class
###########################

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None

    def showtip(self):
        "Display text in tooltip window"
        if self.tipwindow or not self.text:
            return
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


# Example Usage:

# Have a thing:
# screenshot_checkbox = tk.Checkbutton(root, text="Take Screenshot")
# screenshot_checkbox.pack(side=tk.RIGHT, padx=5)

# Make a tooltip:
# createToolTip(screenshot_checkbox, "Capture the screen when clicking")


