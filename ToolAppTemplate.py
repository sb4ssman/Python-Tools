# -*- coding: utf-8 -*-
"""
Created on Sat Jun 6 10:14:14 2024

@author: Thomas
"""


#########################
#                       #
#   TOOL APP TEMPLATE   #
#                       #
#########################

# This is intended to be the skeletal guts of my tools and simple apps



# STANDARD IMPORTS
###############################









# STANDARD CLASSES
###########################

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self):
        # "Display text in tooltip window" 
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
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
        toolTip.showtip()
    def leave(event):
        toolTip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)


# Example Usage:
# screenshot_checkbox = tk.Checkbutton(root, text="Use Screenshot")
# screenshot_checkbox.pack(side=tk.RIGHT, padx=5)
# createToolTip(screenshot_checkbox, "Capture the screen when clicking colors")


