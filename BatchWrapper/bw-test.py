# -*- coding: utf-8 -*-
"""
Created on Fri May 24 01:34:55 2024

@author: Thomas

BatchWrapper: A tool to create Windows batch scripts for running files with command prompt strings and flags.
This tool can be used standalone or as a companion to Windopener.
"""

import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import os
from utils.ToolTips import createToolTip

class BatchWrapper:
    def __init__(self, root, scripts_directory=None, callback=None, file_path=None):
        self.root = root
        self.scripts_directory = scripts_directory
        self.callback = callback
        self.file_path = file_path

        self.root.title("BatchWrapper")
        self.root.geometry("420x840")

        # Initialize variables
        self.init_variables()

        # Setup UI
        self.setup_ui()

        if scripts_directory:
            self.save_directory = scripts_directory
        else:
            self.save_directory = None

        print(f"File path set to: {self.file_path}")

        # Load existing batch file if it exists
        if self.file_path and self.file_path.endswith('.bat'):
            print("Loading existing .bat file...")
            self.load_existing_bat()
            self.update_preview()
        elif self.file_path:
            self.file_label.config(text=os.path.basename(self.file_path))
            self.file_path_display.config(state=tk.NORMAL)
            self.file_path_display.delete(1.0, tk.END)
            self.file_path_display.insert(tk.END, self.file_path)
            self.file_path_display.config(state=tk.DISABLED)
            self.update_preview()
            self.select_target_button.config(text="(Pre-selected)")

    def init_variables(self):
        # Initialize all the variables used in the UI
        self.run_as_admin_var = tk.BooleanVar()
        self.force_new_instance_var = tk.BooleanVar()
        self.min_max_hidden_var = tk.StringVar(value="None")
        self.error_handling_var = tk.StringVar(value="None")
        self.wait_for_exit_var = tk.BooleanVar()
        self.priority_var = tk.StringVar(value="Normal (default)")
        self.log_output_var = tk.BooleanVar()
        self.log_errors_var = tk.BooleanVar()
        self.unbuffered_output_var = tk.BooleanVar()
        self.custom_string_var = tk.StringVar()
        self.custom_arguments_var = tk.StringVar()
        self.env_vars_var = tk.StringVar()
        self.start_in_directory_var = tk.StringVar()
        self.timeout_var = tk.StringVar()
        self.run_as_user_var = tk.StringVar()

        # Add traces for immediate preview updates
        self.timeout_var.trace_add("write", self.update_preview)
        self.timeout_var.trace_add("write", self.validate_timeout)
        self.run_as_user_var.trace_add("write", self.update_preview)

    def setup_ui(self):
        # Setup the main UI components
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.setup_file_selection()
        self.setup_options()
        self.setup_preview_and_buttons()

        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

    def setup_file_selection(self):
        # Setup the file selection section of the UI
        file_selection_frame = tk.Frame(self.main_frame, height=100)
        file_selection_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        file_selection_paned_window = tk.PanedWindow(file_selection_frame, orient=tk.HORIZONTAL, sashwidth=10)
        file_selection_paned_window.pack(fill=tk.BOTH, expand=True, padx=0, pady=(0, 5))

        file_label_frame = tk.PanedWindow(file_selection_paned_window, orient=tk.VERTICAL)
        file_selection_paned_window.add(file_label_frame)

        self.file_label = tk.Label(file_label_frame, text="No target selected:", font=('Arial', 12))
        file_label_frame.add(self.file_label)

        self.select_target_button = tk.Button(file_label_frame, text="Select Target", command=self.select_target)
        file_label_frame.add(self.select_target_button)
        createToolTip(self.select_target_button, "Click to select a target file for the batch script")

        self.file_path_display_frame = tk.LabelFrame(file_selection_paned_window, text="Target Path:")
        file_selection_paned_window.add(self.file_path_display_frame)

        self.file_path_display = tk.Text(self.file_path_display_frame, wrap=tk.WORD, height=3)
        self.file_path_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.file_path_display.config(state=tk.DISABLED)
        createToolTip(self.file_path_display, "Displays the full path of the selected target file")

    def setup_options(self):
        # Setup the options section of the UI
        options_frame = tk.Frame(self.main_frame)
        options_frame.pack(fill=tk.BOTH, expand=True)

        options_paned_window = tk.PanedWindow(options_frame, orient=tk.HORIZONTAL)
        options_paned_window.pack(fill=tk.BOTH, expand=True)

        left_frame = tk.Frame(options_paned_window)
        right_frame = tk.Frame(options_paned_window)

        options_paned_window.add(left_frame)
        options_paned_window.add(right_frame)

        left_frame.pack(side=tk.LEFT, padx=(0, 5), pady=0, fill=tk.BOTH, expand=True)
        right_frame.pack(side=tk.RIGHT, padx=(5, 0), pady=0, fill=tk.BOTH, expand=True)

        # Add options to the left frame
        self.add_option(left_frame, "Run as Administrator", self.run_as_admin_var)
        createToolTip(left_frame.winfo_children()[-1], "Run the script with administrator privileges")

        self.add_option(left_frame, "Force New Instance", self.force_new_instance_var)
        createToolTip(left_frame.winfo_children()[-1], "Force a new instance of the program to run")

        self.add_radio_group(left_frame, "Window State:", self.min_max_hidden_var,
                            [("None", "None"), ("Minimized", "Minimized"), ("Maximized", "Maximized"), ("Hidden", "Hidden")])
        createToolTip(left_frame.winfo_children()[-1], "Set the initial window state of the program")

        self.add_label(left_frame, "Timeout (seconds):")
        self.timeout_entry = tk.Entry(left_frame, textvariable=self.timeout_var, width=10)
        self.timeout_entry.pack(anchor='w', padx=0, pady=0)
        createToolTip(self.timeout_entry, "Set a timeout for the script execution (in seconds)")

        # Add options to the right frame
        self.add_radio_group(right_frame, "Error Handling:", self.error_handling_var,
                            [("None", "None"), ("Ignore Errors", "Ignore Errors"), ("Pause on Error", "Pause on Error")])
        createToolTip(right_frame.winfo_children()[-1], "Choose how to handle errors in the script")

        self.add_option(right_frame, "Wait for Exit", self.wait_for_exit_var)
        createToolTip(right_frame.winfo_children()[-1], "Wait for the program to exit before continuing")

        self.add_option(right_frame, "Log Output", self.log_output_var)
        createToolTip(right_frame.winfo_children()[-1], "Log the program's output to a file")

        self.add_option(right_frame, "Log Errors", self.log_errors_var)
        createToolTip(right_frame.winfo_children()[-1], "Log any errors to a file")

        self.add_option(right_frame, "Unbuffered Output", self.unbuffered_output_var)
        createToolTip(right_frame.winfo_children()[-1], "Use unbuffered output for the program")

        # Add CPU Priority dropdown
        self.add_dropdown(options_frame, "CPU Priority", self.priority_var, 
                        ["Realtime", "High", "Above Normal", "Normal (default)", "Below Normal", "Idle"], width=20)
        createToolTip(options_frame.winfo_children()[-1], "Set the CPU priority for the program")

        # Add custom string entries
        self.add_entry(self.main_frame, "Custom Command String", self.custom_string_var)
        createToolTip(self.main_frame.winfo_children()[-1], "Add a custom command string to the batch file")

        self.add_entry(self.main_frame, "Custom Arguments", self.custom_arguments_var)
        createToolTip(self.main_frame.winfo_children()[-1], "Add custom arguments to the program execution")

        self.add_entry(self.main_frame, "Environment Variables (key=value)", self.env_vars_var)
        createToolTip(self.main_frame.winfo_children()[-1], "Set environment variables for the program")

        self.add_entry(self.main_frame, "Start In Directory", self.start_in_directory_var)
        createToolTip(self.main_frame.winfo_children()[-1], "Set the starting directory for the program")

        # Add Run As Another User entry
        self.add_entry(options_frame, "Run As User:", self.run_as_user_var)
        createToolTip(options_frame.winfo_children()[-1], "Run the program as a specific user")

    def setup_preview_and_buttons(self):
        # Setup the preview section and action buttons
        buttons_frame = tk.Frame(self.main_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))

        save_button = tk.Button(buttons_frame, text="Save .bat File", command=self.save_bat_file)
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        createToolTip(save_button, "Save the generated batch file")

        clear_all_button = tk.Button(buttons_frame, text="Clear All", command=self.clear_all)
        clear_all_button.pack(side=tk.LEFT, padx=(0, 10))
        createToolTip(clear_all_button, "Clear all input fields")

        cancel_button = tk.Button(buttons_frame, text="Cancel/Quit", command=self.root.destroy)
        cancel_button.pack(side=tk.LEFT)
        createToolTip(cancel_button, "Close the BatchWrapper window")

        self.string_preview_label = tk.Label(self.main_frame, text="Command Preview:")
        self.string_preview_label.pack(anchor='w', pady=(10, 0))
        
        self.string_preview = tk.Text(self.main_frame, height=5, wrap='word')
        self.string_preview.pack(fill=tk.BOTH, expand=True, pady=(0, 0))
        self.string_preview.config(state=tk.DISABLED)
        createToolTip(self.string_preview, "Preview of the generated batch command")

    # Helper methods for UI setup
    def add_option(self, parent, text, variable):
        tk.Checkbutton(parent, text=text, variable=variable, command=self.update_preview).pack(anchor='w')

    def add_radio_group(self, parent, label_text, variable, options):
        label = tk.Label(parent, text=label_text)
        label.pack(anchor='w', padx=5, pady=5)
        for text, value in options:
            tk.Radiobutton(parent, text=text, variable=variable, value=value, command=self.update_preview).pack(anchor='w')

    def add_dropdown(self, parent, label_text, variable, options, width=None):
        label = tk.Label(parent, text=label_text)
        label.pack(anchor='w', pady=(10, 0))
        dropdown = tk.OptionMenu(parent, variable, *options, command=self.update_preview)
        dropdown.pack(anchor='w')
        if width:
            dropdown.config(width=width)

    def add_entry(self, parent, label_text, variable):
        label = tk.Label(parent, text=label_text)
        label.pack(anchor='w', pady=(10, 0))
        entry = tk.Entry(parent, textvariable=variable)
        entry.pack(fill=tk.X)
        variable.trace_add("write", self.update_preview)

    def add_label(self, parent, text):
        label = tk.Label(parent, text=text)
        label.pack(anchor='w', padx=5, pady=5)

    def select_target(self):
        # Open a file dialog or use the passed path
        if self.file_path:
            self.file_path = os.path.normpath(self.file_path)
            self.file_label.config(text=os.path.basename(self.file_path))
            self.file_path_display.config(state=tk.NORMAL)
            self.file_path_display.delete(1.0, tk.END)
            self.file_path_display.insert(tk.END, self.file_path)
            self.file_path_display.config(state=tk.DISABLED)
            self.update_preview()
            self.select_target_button.config(text="(Pre-selected)")
            print(f"File path set to: {self.file_path}")
        else:
            file_path = filedialog.askopenfilename()
            if file_path:
                self.file_path = os.path.normpath(file_path)
                self.file_label.config(text=os.path.basename(self.file_path))
                self.file_path_display.config(state=tk.NORMAL)
                self.file_path_display.delete(1.0, tk.END)
                self.file_path_display.insert(tk.END, self.file_path)
                self.file_path_display.config(state=tk.DISABLED)
                self.update_preview()
                print(f"File path selected: {self.file_path}")
                if self.file_path.endswith('.bat'):
                    self.load_existing_bat()
                                         
    def load_existing_bat(self):
        # Load an existing batch file
        print("Inside load_existing_bat method")
        try:
            with open(self.file_path, 'r') as bat_file:
                content = bat_file.read()
                if ":: Generated by BatchWrapper" not in content.splitlines()[0]:
                    messagebox.showerror("Error", "This batch file was not created by BatchWrapper and cannot be edited.")
                    self.clear_all()
                    return
                print("Calling parse_bat_content method")
                self.parse_bat_content(content)
                self.update_preview()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load existing batch file. Error: {str(e)}")
            self.clear_all()

    def parse_bat_content(self, content):
        # Parse the content of an existing batch file
        print("Inside parse_bat_content method")
        lines = content.splitlines()
        for line in lines:
            print(f"Parsing line: {line}")
            if "runas" in line:
                print("Found runas")
                self.run_as_admin_var.set(True)
            if "/d" in line:
                print("Found /d (force new instance)")
                self.force_new_instance_var.set(True)
            if "/min" in line:
                print("Found /min (minimized)")
                self.min_max_hidden_var.set("Minimized")
            elif "/max" in line:
                print("Found /max (maximized)")
                self.min_max_hidden_var.set("Maximized")
            elif "/hide" in line:
                print("Found /hide (hidden)")
                self.min_max_hidden_var.set("Hidden")
            if "2>NUL" in line:
                print("Found 2>NUL (ignore errors)")
                self.error_handling_var.set("Ignore Errors")
            if "|| pause" in line:
                print("Found || pause (pause on error)")
                self.error_handling_var.set("Pause on Error")
            if "/wait" in line:
                print("Found /wait (wait for exit)")
                self.wait_for_exit_var.set(True)
            if "/unbuffered" in line:
                print("Found /unbuffered (unbuffered output)")
                self.unbuffered_output_var.set(True)
            if "1>>output.log" in line:
                print("Found 1>>output.log (log output)")
                self.log_output_var.set(True)
            if "2>>errors.log" in line:
                print("Found 2>>errors.log (log errors)")
                self.log_errors_var.set(True)
            if "/t:" in line:
                timeout_value = line.split("/t:")[1].split()[0]
                print(f"Found timeout: {timeout_value}")
                self.timeout_var.set(timeout_value)
            if "start" in line:
                print("Found start command")
                start_parts = line.split("start")[1].strip().split()
                for part in start_parts:
                    if part.startswith('/'):
                        priority = part.replace('/', '').capitalize() + " (default)"
                        print(f"Found priority: {priority}")
                        self.priority_var.set(priority)
                    if part.startswith("set"):
                        env_vars = part.split('set')[1].strip()
                        print(f"Found env vars: {env_vars}")
                        self.env_vars_var.set(env_vars)
                    if part.startswith('cd'):
                        start_dir = part.split('cd /d')[1].strip()
                        print(f"Found start directory: {start_dir}")
                        self.start_in_directory_var.set(start_dir)

    def validate_timeout(self, *args):
        # Validate that the timeout input is a number
        try:
            value = self.timeout_var.get()
            if value and value != ".":
                float(value)
        except ValueError:
            messagebox.showerror("Invalid Input", "Timeout must be a number.")
            self.timeout_var.set('')

    def clear_all(self):
        # Clear all input fields and reset the UI
        self.file_path = None
        self.file_label.config(text="No target selected:")
        self.file_path_display.config(state=tk.NORMAL)
        self.file_path_display.delete(1.0, tk.END)
        self.file_path_display.config(state=tk.DISABLED)
        self.run_as_admin_var.set(False)
        self.force_new_instance_var.set(False)
        self.min_max_hidden_var.set("None")
        self.error_handling_var.set("None")
        self.wait_for_exit_var.set(False)
        self.priority_var.set("Normal (default)")
        self.log_output_var.set(False)
        self.log_errors_var.set(False)
        self.unbuffered_output_var.set(False)
        self.custom_string_var.set("")
        self.custom_arguments_var.set("")
        self.env_vars_var.set("")
        self.start_in_directory_var.set("")
        self.timeout_var.set("")
        self.run_as_user_var.set("") 
        self.string_preview.config(state=tk.NORMAL)
        self.string_preview.delete(1.0, tk.END)
        self.string_preview.config(state=tk.DISABLED)
        self.update_preview()

    def generate_command(self):
        # Generate the batch command based on the current settings
        runas_command, commands = self.build_command_list()
        bat_content = self.build_bat_content(runas_command, commands)
        return bat_content

    def build_command_list(self):
        # Build the list of commands based on the current settings
        commands = []
        run_as_user = self.run_as_user_var.get()
        if self.run_as_admin_var.get() and run_as_user:
            runas_command = f'runas /user:{run_as_user}'
        elif self.run_as_admin_var.get():
            runas_command = 'runas /user:Administrator'
        elif run_as_user:
            runas_command = f'runas /user:{run_as_user}'
        else:
            runas_command = ''

        if self.force_new_instance_var.get():
            commands.append("/d")
        state = self.min_max_hidden_var.get()
        if state == "Minimized":
            commands.append("/min")
        elif state == "Maximized":
            commands.append("/max")
        elif state == "Hidden":
            commands.append("/hide")

        priority = self.priority_var.get()
        if priority != "Normal (default)":
            commands.append(f"/{priority.lower().replace(' ', '')}")
        
        error_handling = self.error_handling_var.get()
        if error_handling == "Ignore Errors":
            commands.append("2>NUL")
        elif error_handling == "Pause on Error":
            commands.append("|| pause")
        
        if self.wait_for_exit_var.get():
            commands.append("/wait")
        
        if self.unbuffered_output_var.get():
            commands.append("/unbuffered")

        timeout = self.timeout_var.get()
        if timeout:
            commands.append(f"/t:{timeout}")
        
        if self.log_output_var.get():
            commands.append("1>>output.log")
        if self.log_errors_var.get():
            commands.append("2>>errors.log")
        
        return runas_command, commands

    def build_bat_content(self, runas_command, commands):
        # Build the final batch file content
        custom_string = self.custom_string_var.get()
        custom_arguments = self.custom_arguments_var.get()
        env_vars = self.env_vars_var.get()
        start_in_directory = self.start_in_directory_var.get()

        bat_content = '@echo off\n'
        if custom_string:
            bat_content += f'{custom_string}\n'
        if env_vars:
            bat_content += f'set {env_vars}\n'
        if start_in_directory:
            bat_content += f'cd /d "{start_in_directory}"\n'

        if runas_command:
            bat_content += f'{runas_command} '
        
        bat_content += f'start {" ".join(commands)} "{self.file_path}" {custom_arguments}\n'
        
        return bat_content

    def save_bat_file(self):
        # Save the generated batch file
        if not self.file_path:
            messagebox.showerror("Error", "No file selected.")
            return

        default_filename = os.path.splitext(os.path.basename(self.file_path))[0] + "_bw.bat"
        default_filepath = os.path.join(self.scripts_directory if self.scripts_directory else "", default_filename)

        bat_path = filedialog.asksaveasfilename(defaultextension=".bat", filetypes=[("Batch files", "*.bat")], initialfile=default_filename)
        if not bat_path:
            return

        bat_command = self.generate_command()
        timestamp = f":: Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        special_comment = ":: Generated by BatchWrapper\n" + timestamp + "\n"

        try:
            with open(bat_path, 'w') as bat_file:
                bat_file.write(special_comment + bat_command)
            messagebox.showinfo("Success", f"Batch file saved to {bat_path}")
            if self.callback:
                self.callback(os.path.normpath(bat_path))
                self.root.destroy()
            else:
                self.clear_all()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save batch file. Error: {str(e)}")

    def update_preview(self, *args):
        # Update the command preview
        if not self.file_path:
            return

        bat_content = self.generate_command()

        self.string_preview.config(state=tk.NORMAL)
        self.string_preview.delete(1.0, tk.END)
        self.string_preview.insert(tk.END, bat_content)
        self.string_preview.config(state=tk.DISABLED)

def main():
    root = tk.Tk()
    app = BatchWrapper(root)
    root.mainloop()

if __name__ == "__main__":
    main()