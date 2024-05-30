# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 11:52:19 2024

@author: Thomas
"""

import tkinter as tk
import ctypes
from ctypes import wintypes

# Define necessary structures and constants
class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long)]

GetForegroundWindow = ctypes.windll.user32.GetForegroundWindow
GetWindowRect = ctypes.windll.user32.GetWindowRect
SetWindowPos = ctypes.windll.user32.SetWindowPos

HWND_TOP = 0
SWP_SHOWWINDOW = 0x0040

# Function to get the actual position of the current foreground window
def get_window_pos():
    rect = RECT()
    hwnd = GetForegroundWindow()  # Get handle to the foreground window
    GetWindowRect(hwnd, ctypes.byref(rect))  # Get window coordinates
    print(f"Window top-left corner is at: ({rect.left},{rect.top})")  # Print the top-left corner

# Function to move the current window to (0,0)
def move_window_to_zero():
    hwnd = GetForegroundWindow()
    SetWindowPos(hwnd, HWND_TOP, 0, 0, 0, 0, SWP_SHOWWINDOW)
    get_window_pos()  # Call to print the new position

# Function to move the Tkinter window to (0,0) on the screen
def move_window(event):
    move_window_to_zero()

# Create the main application window
root = tk.Tk()
root.title("Calibration Window")

# Make the window small and less obtrusive
root.geometry("100x100+300+300")  # Start it somewhere visible

# Bind a mouse click to attempt moving the window to (0,0)
root.bind("<Button-1>", move_window)

# Run the application
root.mainloop()
