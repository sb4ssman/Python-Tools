# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 11:05:55 2024

@author: Thomas
"""

# This this tool places a window at Window's location 0,0
# On calibration it detects the location of the window using the monitor's x,y coordinates
# Then it returns the difference between the close and the window's origin

# The offset itself measures the location of the window's virtual desktop origin realtive to the 0,0 pixel on the primary monitor. 

# This is useful for large format displays or TVs acting as computer monitors or any other instance where the Window's virtual desktop does not align with the monitor. 

import tkinter as tk
from tkinter import ttk, messagebox

# This is called in standalone: function replies to the user with the offset in a messagebox
def detect_offset():
    offsetX, offsetY = calibrate_offset()
    messagebox.showinfo("Offset Detected", f"The Windows virtual desktop origin is translated:\n"
                                           f"        {offsetX} pixels horizontally\n"
                                           f"        {offsetY} pixels vertically\n"
                                           f"from your primary monitor's origin pixel.")

# Importable function to gather the offset for calibration
def calibrate_offset():
    offsetX, offsetY = 0, 0     # Initialize offsets

    # define calibration event
    def on_calibrate():
        nonlocal offsetX, offsetY
        # Get deets
        x_o = root.winfo_x()
        y_o = root.winfo_y()
        print(f"Calibration window closed @ {x_o}, {y_o}")
        
        # Compute offset (assuming 0,0 is expected at the monitor's origin pixel, and the user got the window's critical pixel there)
        offsetX = -x_o  # This formula is zero minus x_origin
        offsetY = -y_o
        print(f"Offset: {offsetX}, {offsetY}")
        
        root.quit() # Exit the main loop

    # Create a simple window
    root = tk.Tk()
    root.title('Offset Calibrator')
    root.geometry("300x240+0+0")  # Place at Windows' version of (0, 0)
    root.wm_attributes("-topmost", 1) # This line sets the window to stay on top

    print("Calibration window instantiated at Window's coordinate (0, 0)")

    instructions_font = ("", 12)
    # Text instructions above the button
    instructions = tk.Label(root, text="This window was placed at (0,0).\n"
                                       "Move this window to the top-left corner\n"
                                       "of your primary monitor, then click\n"
                                       "'Calibrate'.\n\n"
                                       "Snapping to the corner works.\n"
                                       "Maximize does NOT.",
                            justify=tk.LEFT, padx=10, font=instructions_font)
    instructions.pack(pady=(10, 0))  # Add some padding above and below the label

    button_font = ("", 16)
    button = tk.Button(root, text="Calibrate", command=on_calibrate, font=button_font)
    button.pack(fill="both", expand=True, padx=20, pady=20)

    root.mainloop() # Start the tkinter event loop, wait for calibration
    root.destroy() # destroy the window immediately

    # Return the results
    return offsetX, offsetY 

if __name__ == "__main__":
    detect_offset()