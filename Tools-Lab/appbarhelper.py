# -*- coding: utf-8 -*-
"""
Created on Tue Jul 9 13:521:52 2024

@author: Thomas
"""

# appbarhelper.py

# Returns details about the taskbar on the PRIMARY MONITOR:
#     dict: A dictionary containing the following keys:
#         - "orientation" (str): The orientation of the taskbar ("left", "top", "right", "bottom", or "unknown").
#         - "position" (tuple): The position of the taskbar as a tuple of (left, top, right, bottom) coordinates.
#         - "size" (int): The size of the taskbar in pixels.


# This module provides functions to interact with the Windows taskbar (AppBar) using the Windows API.
# It allows retrieving information about the taskbar's position, size, and orientation.

# Functions:
# - get_appbardata(): Retrieves raw AppBar data from the Windows API.
# - get_taskbar_info(appbardata): Processes raw AppBar data to return taskbar information.

# Usage:
#     from appbarhelper import get_appbardata, get_taskbar_info

#     appbardata = get_appbardata()
#     taskbar_info = get_taskbar_info(appbardata)
#     print(taskbar_info)


import ctypes
from ctypes import wintypes

# Define the APPBARDATA structure used by the Windows API
class APPBARDATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("hWnd", ctypes.c_void_p),
        ("uCallbackMessage", ctypes.c_uint),
        ("uEdge", ctypes.c_uint),
        ("rc", ctypes.c_long * 4),
        ("lParam", ctypes.c_long),
    ]

# Windows API constant for getting taskbar position
ABM_GETTASKBARPOS = 0x00000005

def get_appbardata():
    # Retrieves raw AppBar data from the Windows API. Returns: APPBARDATA: A ctypes structure containing raw AppBar data.
    appbardata = APPBARDATA()
    appbardata.cbSize = ctypes.sizeof(appbardata)
    ctypes.windll.shell32.SHAppBarMessage(ABM_GETTASKBARPOS, ctypes.byref(appbardata))
    return appbardata

def get_taskbar_info(appbardata):
    # Processes raw AppBar data to return taskbar information.

    # Args:
    # appbardata (APPBARDATA): Raw AppBar data from get_appbardata()

    # Returns:
    # dict: A dictionary containing processed taskbar information:
    #     - orientation: The taskbar's orientation ('left', 'top', 'right', 'bottom', or 'unknown')
    #     - position: A tuple of (left, top, right, bottom) coordinates of the taskbar
    #     - size: The width or height of the taskbar in pixels
    taskbar_edge = appbardata.uEdge
    taskbar_rect = tuple(appbardata.rc)
    
    orientations = {0: 'left', 1: 'top', 2: 'right', 3: 'bottom'}
    orientation = orientations.get(taskbar_edge, 'unknown')
    
    if orientation in ['left', 'right']:
        taskbar_size = taskbar_rect[2] - taskbar_rect[0]
    elif orientation in ['top', 'bottom']:
        taskbar_size = taskbar_rect[3] - taskbar_rect[1]
    else:
        taskbar_size = 0
    
    return {
        "orientation": orientation,
        "position": taskbar_rect,
        "size": taskbar_size
    }

if __name__ == "__main__":
    # Example usage
    appbardata = get_appbardata()
    taskbar_info = get_taskbar_info(appbardata)
    print(taskbar_info)


# Early version

# import ctypes

# class APPBARDATA(ctypes.Structure):
#     _fields_ = [
#         ("cbSize", ctypes.c_uint),
#         ("hWnd", ctypes.c_void_p),
#         ("uCallbackMessage", ctypes.c_uint),
#         ("uEdge", ctypes.c_uint),
#         ("rc", ctypes.c_long * 4),
#         ("lParam", ctypes.c_long),
#     ]

# ABM_GETTASKBARPOS = 0x00000005

# def get_taskbar_info():
#     appbardata = APPBARDATA()
#     appbardata.cbSize = ctypes.sizeof(appbardata)
#     ctypes.windll.shell32.SHAppBarMessage(ABM_GETTASKBARPOS, ctypes.byref(appbardata))
    
#     taskbar_edge = appbardata.uEdge
#     taskbar_rect = tuple(appbardata.rc)
    
#     if taskbar_edge == 0:
#         orientation = 'left'
#         taskbar_size = taskbar_rect[2] - taskbar_rect[0]
#     elif taskbar_edge == 1:
#         orientation = 'top'
#         taskbar_size = taskbar_rect[3] - taskbar_rect[1]
#     elif taskbar_edge == 2:
#         orientation = 'right'
#         taskbar_size = taskbar_rect[2] - taskbar_rect[0]
#     elif taskbar_edge == 3:
#         orientation = 'bottom'
#         taskbar_size = taskbar_rect[3] - taskbar_rect[1]
#     else:
#         orientation = 'unknown'
#         taskbar_size = 0
    
#     return {
#         "orientation": orientation,
#         "position": taskbar_rect, # (top_left_x, top_left_y, bottom_right_x, bottom_right_y)
#         "size": taskbar_size
#     }

# if __name__ == "__main__":
#     taskbar_info = get_taskbar_info()
#     print(taskbar_info)