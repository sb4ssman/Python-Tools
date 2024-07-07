# -*- coding: utf-8 -*-
"""
Created on Tue Oct 24 15:22:54 2023

@author: Thomas
"""

import pyautogui
import time

def get_mouse_position():
    time.sleep(5)  # Gives you 5 seconds to position your mouse
    return pyautogui.position()

if __name__ == "__main__":
    print(get_mouse_position())
