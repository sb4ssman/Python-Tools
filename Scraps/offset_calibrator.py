# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 11:05:55 2024

@author: Thomas
"""

# This is a standalone manual tool to calculate the offset, if any, of Windows' window placement against the absolute x,y pixels in the top left of the screen.

import pyautogui
import tkinter as tk

def calibrate_offset():
    # Create a simple window
    root = tk.Tk()
    root.geometry("250x150+0+0")  # Attempt to position at the top-left corner
    
    # Text instructions above the button
    instructions = tk.Label(root, text="This window was placed at (0,0)\n"
                                        "Move this window to the top-left corner\n"
                                        "of your screen, then click 'Calibrate'.\n"
                                        "Snap to the upper left corner works.",
                            justify=tk.LEFT, padx=10)
    instructions.pack(pady=(10, 0))  # Add some padding above and below the label

    
    def on_calibrate():
        # Get the actual position of the window
        x0 = root.winfo_x()
        y0 = root.winfo_y()
        print(f"Calibration: Window is at {x0}, {y0}")
        
        # Compute offset (assuming 0,0 is expected)
        global offsetX, offsetY
        offsetX = -x0  # If the window is at -7 for x, this will be 7
        offsetY = -y0
        print(f"Offset: {offsetX}, {offsetY}")
        
        return [offsetX,offsetY]
        
        root.destroy()


    button = tk.Button(root, text="Calibrate", command=on_calibrate)
    button.pack(pady=20)

    root.mainloop()

# Initial offsets
offsetX, offsetY = 0, 0

if __name__ == "__main__":
    calibrate_offset()
    # Now, use offsetX and offsetY for future window positioning adjustments
