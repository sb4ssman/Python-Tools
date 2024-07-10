# -*- coding: utf-8 -*-
"""
Created on Tue Jul 9 13:41:34 2024

@author: Thomas
"""

# monitorinfoexhelper.py

# Retrieves information about ALL connected monitors.

# Returns:
#     list: A list of dictionaries, where each dictionary represents a monitor and contains the following keys:
#         - "device_name" (str): The name of the monitor device.
#         - "screen_coords" (tuple): The screen coordinates of the monitor as a tuple of (left, top, right, bottom).
#         - "work_area_coords" (tuple): The work area coordinates of the monitor as a tuple of (left, top, right, bottom).
#         - "is_primary" (bool): Indicates whether the monitor is the primary monitor.
#         - "taskbar_autohide" (bool): Indicates whether the taskbar is set to auto-hide on the monitor.
#         - "taskbar_position" (tuple): The position of the taskbar on the monitor as a tuple of (left, top, right, bottom) coordinates.
#         - "taskbar_edge" (int): The edge of the screen where the taskbar is located (0: left, 1: top, 2: right, 3: bottom).



"""
monitorinfoexhelper.py

This module provides functions to retrieve detailed information about all connected monitors
in a Windows environment, including taskbar information for each monitor.

Functions:
- get_monitors_info(): Retrieves detailed information about all connected monitors.

Usage:
    from monitorinfoexhelper import get_monitors_info

    monitors_info = get_monitors_info()
    for monitor in monitors_info:
        print(monitor)
"""

import ctypes
from ctypes import wintypes
from appbarhelper import get_appbardata, get_taskbar_info, APPBARDATA

# Define the MONITORINFOEX structure used by the Windows API
class MONITORINFOEX(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
        ("szDevice", wintypes.WCHAR * 32)
    ]

# Windows API constant for auto-hide taskbar state
ABS_AUTOHIDE = 0x0000001

def get_monitors_info():
    """
    Retrieves detailed information about all connected monitors.

    Returns:
    list: A list of dictionaries, each containing information about a monitor:
        - device_name: The name of the monitor device
        - screen_coords: A tuple of (left, top, right, bottom) coordinates of the entire screen
        - work_area_coords: A tuple of (left, top, right, bottom) coordinates of the work area
        - is_primary: Boolean indicating if this is the primary monitor
        - taskbar_autohide: Boolean indicating if the taskbar is set to auto-hide
        - taskbar_position: A tuple of (left, top, right, bottom) coordinates of the taskbar
        - taskbar_edge: The edge where the taskbar is located (0: left, 1: top, 2: right, 3: bottom)
        - taskbar_orientation: The orientation of the taskbar ('left', 'top', 'right', 'bottom', or 'unknown')
        - taskbar_size: The width or height of the taskbar in pixels
    """
    monitors = []
    
    def enum_monitors_callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
        # Get monitor info
        monitor_info = MONITORINFOEX()
        monitor_info.cbSize = ctypes.sizeof(MONITORINFOEX)
        ctypes.windll.user32.GetMonitorInfoW(hMonitor, ctypes.byref(monitor_info))
        
        # Get taskbar info
        appbardata = get_appbardata()
        appbardata.hWnd = hMonitor
        taskbar_info = get_taskbar_info(appbardata)
        
        # Get taskbar state (for auto-hide)
        taskbar_state = ctypes.windll.shell32.SHAppBarMessage(4, ctypes.byref(appbardata))
        
        monitor_data = {
            "device_name": monitor_info.szDevice,
            "screen_coords": (monitor_info.rcMonitor.left, monitor_info.rcMonitor.top, monitor_info.rcMonitor.right, monitor_info.rcMonitor.bottom),
            "work_area_coords": (monitor_info.rcWork.left, monitor_info.rcWork.top, monitor_info.rcWork.right, monitor_info.rcWork.bottom),
            "is_primary": bool(monitor_info.dwFlags & 1),
            "taskbar_autohide": bool(taskbar_state & ABS_AUTOHIDE),
            "taskbar_position": taskbar_info["position"],
            "taskbar_edge": appbardata.uEdge,
            "taskbar_orientation": taskbar_info["orientation"],
            "taskbar_size": taskbar_info["size"]
        }
        
        monitors.append(monitor_data)
        return True

    # Enumerate all monitors
    enum_monitors_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)
    ctypes.windll.user32.EnumDisplayMonitors(None, None, enum_monitors_proc(enum_monitors_callback), 0)
    
    return monitors

if __name__ == "__main__":
    # Example usage
    monitors_info = get_monitors_info()
    for monitor_info in monitors_info:
        print(monitor_info)
        print("---")





# import ctypes
# from ctypes import wintypes
# from appbarhelper import get_appbardata, get_taskbar_info, APPBARDATA

# class MONITORINFOEX(ctypes.Structure):
#     _fields_ = [
#         ("cbSize", wintypes.DWORD),
#         ("rcMonitor", wintypes.RECT),
#         ("rcWork", wintypes.RECT),
#         ("dwFlags", wintypes.DWORD),
#         ("szDevice", wintypes.WCHAR * 32)
#     ]

# def get_monitors_info():
#     monitors = []
    
#     def enum_monitors_callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
#         monitor_info = MONITORINFOEX()
#         monitor_info.cbSize = ctypes.sizeof(MONITORINFOEX)
#         ctypes.windll.user32.GetMonitorInfoW(hMonitor, ctypes.byref(monitor_info))
        
#         appbardata = get_appbardata()
#         appbardata.hWnd = hMonitor
#         taskbar_info = get_taskbar_info(appbardata)
        
#         monitor_data = {
#             "device_name": monitor_info.szDevice,
#             "screen_coords": (monitor_info.rcMonitor.left, monitor_info.rcMonitor.top, monitor_info.rcMonitor.right, monitor_info.rcMonitor.bottom),
#             "work_area_coords": (monitor_info.rcWork.left, monitor_info.rcWork.top, monitor_info.rcWork.right, monitor_info.rcWork.bottom),
#             "is_primary": bool(monitor_info.dwFlags & 1),
#             "taskbar_info": taskbar_info
#         }
        
#         monitors.append(monitor_data)
#         return True

#     enum_monitors_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)
#     ctypes.windll.user32.EnumDisplayMonitors(None, None, enum_monitors_proc(enum_monitors_callback), 0)
    
#     return monitors

# if __name__ == "__main__":
#     monitors_info = get_monitors_info()
#     for monitor_info in monitors_info:
#         print(monitor_info)
#         print("---")





















# import ctypes
# from ctypes import wintypes

# # ... (previous code for APPBARDATA and other structures)

# class MONITORINFOEX(ctypes.Structure):
#     _fields_ = [
#         ("cbSize", wintypes.DWORD),
#         ("rcMonitor", wintypes.RECT),
#         ("rcWork", wintypes.RECT),
#         ("dwFlags", wintypes.DWORD),
#         ("szDevice", wintypes.WCHAR * 32)
#     ]

# def enum_monitors_callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
#     monitor_info = MONITORINFOEX()
#     monitor_info.cbSize = ctypes.sizeof(MONITORINFOEX)
#     ctypes.windll.user32.GetMonitorInfoW(hMonitor, ctypes.byref(monitor_info))
    
#     # Retrieve taskbar state for the monitor
#     appbardata = APPBARDATA()
#     appbardata.cbSize = ctypes.sizeof(APPBARDATA)
#     appbardata.hWnd = hMonitor
#     taskbar_state = ctypes.windll.shell32.SHAppBarMessage(ABM_GETSTATE, ctypes.byref(appbardata))
    
#     # Retrieve taskbar position and size for the monitor
#     ctypes.windll.shell32.SHAppBarMessage(ABM_GETTASKBARPOS, ctypes.byref(appbardata))
    
#     # Store monitor and taskbar information
#     monitor_data = {
#         "device_name": monitor_info.szDevice,
#         "screen_coords": (monitor_info.rcMonitor.left, monitor_info.rcMonitor.top, monitor_info.rcMonitor.right, monitor_info.rcMonitor.bottom),
#         "work_area_coords": (monitor_info.rcWork.left, monitor_info.rcWork.top, monitor_info.rcWork.right, monitor_info.rcWork.bottom),
#         "is_primary": bool(monitor_info.dwFlags & 1),
#         "taskbar_autohide": bool(taskbar_state & ABS_AUTOHIDE),
#         "taskbar_position": (appbardata.rc[0], appbardata.rc[1], appbardata.rc[2], appbardata.rc[3]),
#         "taskbar_edge": appbardata.uEdge,
#         "taskbar_orientation": orientation,
#         "taskbar_size": taskbar_size
#     }
    
#     # Append monitor data to the list
#     monitor_data_list.append(monitor_data)
    
#     return True

# # Enumerate monitors and retrieve taskbar information
# monitor_data_list = []
# enum_monitors_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)
# ctypes.windll.user32.EnumDisplayMonitors(None, None, enum_monitors_proc(enum_monitors_callback), 0)

# # Print the collected monitor and taskbar data
# for monitor_data in monitor_data_list:
#     print(f"Monitor: {monitor_data['device_name']}")
#     print(f"Screen Coordinates: {monitor_data['screen_coords']}")
#     print(f"Work Area Coordinates: {monitor_data['work_area_coords']}")
#     print(f"Is Primary: {monitor_data['is_primary']}")
#     print(f"Taskbar Auto-Hide: {monitor_data['taskbar_autohide']}")
#     print(f"Taskbar Position: {monitor_data['taskbar_position']}")
#     print(f"Taskbar Edge: {monitor_data['taskbar_edge']}")
#     print("---")


# def get_monitors_info():
#     pass


# if __name__ == "__main__":
#     monitors_info = get_monitors_info()
#     for monitor_info in monitors_info:
#         print(monitor_info)
#         print("---")