# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 11:05:55 2024

@author: Thomas
"""

# This this tool places a window at Window's location 0,0
# On calibration it detects the location of the window using the monitor's x,y coordinates
# Then it returns the difference

# This is useful for large format displays or TVs acting as computer monitors or any other instance where the Window's virtual desktop does not align with the monitor. 



import pyautogui
import tkinter as tk



def calibrate_offset():
    offsetX, offsetY = 0, 0     # Initialize offsets

    def on_calibrate():
        nonlocal offsetX, offsetY # Use nonlocal to modify outer scope variables
        # Get the *reported* position of the window
        x0 = root.winfo_x()
        y0 = root.winfo_y()
        print(f"Calibration: Window is at {x0}, {y0}")
        
        # Compute offset (assuming 0,0 is expected)
        offsetX = -x0  # This formula is zero minus x0 
        offsetY = -y0
        print(f"Offset: {offsetX}, {offsetY}") # Window's origin is shifted in relation to the primary monitor origin pixel
        
        root.quit() # Exit the main loop
        

    # Create a simple window
    root = tk.Tk()
    root.title('Offset Calibrator')
    root.geometry("300x200+0+0")  # Place at Windows' version of (0, 0)
    root.wm_attributes("-topmost", 1) # This line sets the window to stay on top


    instructions_font = ("Helvetica", 12)
    # Text instructions above the button
    instructions = tk.Label(root, text="This window was placed at (0,0).\n"
                                        "Move this window to the top-left corner\n"
                                        "of your primary monitor, then click\n"
                                        "'Calibrate'.\n\n"
                                        "Snapping to the corner works.",
                            justify=tk.LEFT, padx=10, font=instructions_font)
    instructions.pack(pady=(10, 0))  # Add some padding above and below the label

    



    button_font = ("Helvetica", 16)
    button = tk.Button(root, text="Calibrate", command=on_calibrate, font=button_font)
    button.pack(fill="both", expand=True, padx=20, pady=20)

    

    root.mainloop() # Start the tkinter event loop, wait for calibration
    root.destroy() # destroy the window after loop exits
    
    # Return the results
    return offsetX, offsetY 



# One-line app
if __name__ == "__main__":
    print(calibrate_offset())
    
