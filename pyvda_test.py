import os
import time
import subprocess
import pyvda
import pygetwindow as gw
from tkinter import Tk, Button, Listbox, Scrollbar, END

def open_file(file_path):
    proc = subprocess.Popen(file_path, shell=True)
    return proc

def move_window_to_desktop(hwnd, desktop_number):
    desktops = pyvda.VirtualDesktopManager().desktops
    if desktop_number < len(desktops):
        desktop = desktops[desktop_number]
        pyvda.VirtualDesktop(desktop).move_window(hwnd)
    else:
        print(f"Desktop {desktop_number} does not exist.")

def get_hwnd_from_title(title):
    windows = gw.getWindowsWithTitle(title)
    return [w._hWnd for w in windows if w.visible]

def open_file_on_desktop(file_path, desktop_number):
    proc = open_file(file_path)
    time.sleep(5)  # Allow more time for the window to open

    hwnd_list = []
    for _ in range(10):  # Retry multiple times to find the window
        hwnd_list = get_hwnd_from_title(os.path.basename(file_path))
        if hwnd_list:
            break
        print(f"Retrying to find window for {file_path}, attempt {_ + 1}")
        time.sleep(1)

    if hwnd_list:
        for hwnd in hwnd_list:
            print(f"Found window for {file_path} with HWND: {hwnd}")
            move_window_to_desktop(hwnd, desktop_number)
    else:
        print(f"Could not find window for {file_path}")

def open_file_list(file_list):
    for file_path, monitor, position, desktop in file_list:
        print(f"Opening {file_path} on monitor {monitor} at position {position} on desktop {desktop}")
        open_file_on_desktop(file_path, int(desktop))

def load_file_list(file_path):
    file_list = []
    with open(file_path, 'r') as file:
        for line in file:
            parts = line.strip().split(',')
            if len(parts) == 4:
                path, monitor, position, desktop = parts
                file_list.append((path, monitor, position, desktop))
    return file_list

def on_open_selected_file(listbox):
    selected_file = listbox.get(listbox.curselection())
    file_path = os.path.join(projects_directory, selected_file)
    file_list = load_file_list(file_path)
    open_file_list(file_list)

# GUI setup
def create_test_app():
    root = Tk()
    root.title("Test App")
    root.geometry("400x300")

    listbox = Listbox(root)
    listbox.pack(fill="both", expand=True)

    scrollbar = Scrollbar(listbox)
    scrollbar.pack(side="right", fill="y")
    listbox.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=listbox.yview)

    for file_name in os.listdir(projects_directory):
        if file_name.endswith(".txt"):
            listbox.insert(END, file_name)

    open_button = Button(root, text="Open List", command=lambda: on_open_selected_file(listbox))
    open_button.pack(side="left", padx=20, pady=20)

    quit_button = Button(root, text="Quit", command=root.quit)
    quit_button.pack(side="right", padx=20, pady=20)

    root.mainloop()

if __name__ == "__main__":
    projects_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'projects')
    create_test_app()
