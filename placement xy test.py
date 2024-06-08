# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 10:43:38 2024

@author: Thomas
"""

import os
import random
import time
import pyautogui
import pygetwindow as gw
import subprocess

def get_system_info():
    screen_width, screen_height = pyautogui.size()
    print(f"Screen size: {screen_width}x{screen_height}")
    # Additional system information can be gathered as needed

def open_file_at_position(file_path, x, y):
    # Attempt to open the file using the default application
    if os.path.exists(file_path):
        os.startfile(file_path)
        time.sleep(2)  # Wait a bit for the application to open
        
        # Move the window
        windows = gw.getWindowsWithTitle(os.path.basename(file_path))
        if windows:
            window = windows[0]
            window.moveTo(x, y)
            print(f"Moved window to: {x}, {y}")
        else:
            print("Window not found.")
    else:
        print("File does not exist.")

if __name__ == "__main__":
    get_system_info()

    # Example file paths (replace these with your actual file paths)
    files = [
        "<path_to_file>"

    ]

    # Input coordinates
    x = int(input("Enter X coordinate: "))
    y = int(input("Enter Y coordinate: "))

    # Open a random file at the specified position
    file_to_open = random.choice(files)
    print(f"Opening {file_to_open}")
    open_file_at_position(file_to_open, x, y)
