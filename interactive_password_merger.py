import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from urllib.parse import urlparse
import datetime

"""
Script: Password CSV Merger (Interactive)
Author: sb4ssman
Date: 2026-01-17
Description: 
    Merges multiple password CSV exports into a single Bitwarden-compatible CSV.
    Provides an interactive GUI to resolve conflicts.
    Ensures all sources are visible during comparison.
"""

# --- CONFIGURATION ---
OUTPUT_FILENAME = 'final_clean_import.csv'

class PasswordMergerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw() # Hide main window initially
        self.conflicts = []
        self.resolved_data = []
        self.current_conflict_index = 0
        self.all_sources = set()
        self.output_dir = ""
        
    def normalize_url(self, url):
        if not isinstance(url, str) or not url.strip():
            return ''
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        try:
            parsed = urlparse(url)
            return f"{parsed.netloc.replace('www.', '')}{parsed.path.rstrip('/')}"
        except:
            return url

    def load_csvs(self, file_paths):
        all_dfs = []
        print(f"Loading {len(file_paths)} files...")
        
        for file_path in file_paths:
            try:
                df = pd.read_csv(file_path)
                # Normalize headers
                cols = {c.lower(): c for c in df.columns}
                rename_map = {}
                
                # Map common headers to standard keys
                if 'login_uri' in cols: rename_map[cols['login_uri']] = 'url'
                elif 'url' in cols: rename_map[cols['url']] = 'url'
                
                if 'login_username' in cols: rename_map[cols['login_username']] = 'username'
                elif 'username' in cols: rename_map[cols['username']] = 'username'
                
                if 'login_password' in cols: rename_map[cols['login_password']] = 'password'
                elif 'password' in cols: rename_map[cols['password']] = 'password'
                
                if 'name' in cols: rename_map[cols['name']] = 'name'
                
                df.rename(columns=rename_map, inplace=True)
                
                # Ensure required columns exist
                for req in ['url', 'username', 'password', 'name']:
                    if req not in df.columns:
                        df[req] = ''
                
                df = df[['url', 'username', 'password', 'name']].fillna('')
                df['source_file'] = os.path.basename(file_path)
                df['norm_url'] = df['url'].apply(self.normalize_url)
                
                all_dfs.append(df)
                print(f" -> Loaded {len(df)} rows from {os.path.basename(file_path)}")
            except Exception as e:
                print(f" [!] Error reading {file_path}: {e}")

        if not all_dfs:
            return pd.DataFrame()
        
        full_df = pd.concat(all_dfs, ignore_index=True)
        self.all_sources = set(full_df['source_file'].unique())
        return full_df

    def run(self):
        # 1. Select Files
        print("Waiting for user to select files...")
        files = filedialog.askopenfilenames(title="Select Password CSV Files to Merge", filetypes=[("CSV Files", "*.csv")])
        if not files: 
            print("No files selected. Exiting.")
            return
        
        self.output_dir = os.path.dirname(files[0])

        # 2. Load Data
        df = self.load_csvs(files)
        if df.empty:
            messagebox.showerror("Error", "No CSVs found or could not parse data.")
            return

        # 3. Group and Detect Conflicts
        print("Analyzing for conflicts...")
        grouped = df.groupby(['norm_url', 'username'])
        
        for (url, user), group in grouped:
            unique_passwords = group['password'].unique()
            unique_passwords = [p for p in unique_passwords if p] # Remove empty
            
            if len(unique_passwords) <= 1:
                # No conflict (or only 1 valid password)
                best_row = group.iloc[0].to_dict()
                if len(unique_passwords) == 1:
                    best_row['password'] = unique_passwords[0]
                self.resolved_data.append(best_row)
            else:
                # CONFLICT DETECTED
                # Create a conflict object
                conflict_entries = []
                for pwd in unique_passwords:
                    # Find the source file for this password
                    sources = group[group['password'] == pwd]['source_file'].tolist()
                    conflict_entries.append({
                        'password': pwd,
                        'sources': ", ".join(sources)
                    })
                
                self.conflicts.append({
                    'url': group.iloc[0]['url'],
                    'norm_url': url,
                    'username': user,
                    'name': group.iloc[0]['name'],
                    'options': conflict_entries
                })

        print(f"Analysis complete. Found {len(self.conflicts)} conflicts to resolve.")
        print(f"Auto-resolved {len(self.resolved_data)} clean entries.")

        # 4. Launch Wizard if conflicts exist
        if self.conflicts:
            print("Launching Conflict Wizard...")
            self.launch_wizard()
        else:
            self.save_results()

    def launch_wizard(self):
        self.root.deiconify()
        self.root.title(f"Conflict Resolution Wizard ({len(self.conflicts)} conflicts)")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # UI Setup
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header Info
        self.lbl_site = ttk.Label(main_frame, text="", font=("Arial", 14, "bold"))
        self.lbl_site.pack(pady=(0, 5))
        
        self.lbl_user = ttk.Label(main_frame, text="", font=("Arial", 12))
        self.lbl_user.pack(pady=(0, 20))
        
        # Comparison Area
        self.compare_frame = ttk.Frame(main_frame)
        self.compare_frame.pack(fill=tk.BOTH, expand=True)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=20)
        
        # Save & Quit Button
        ttk.Button(btn_frame, text="Save Progress & Quit", command=self.on_close).pack(side=tk.LEFT, padx=5)
        
        self.progress_var = tk.StringVar()
        ttk.Label(btn_frame, textvariable=self.progress_var).pack(side=tk.RIGHT)
        
        self.show_conflict(0)
        self.root.mainloop()
        
    def on_close(self):
        if messagebox.askyesno("Quit", "Save current progress and quit? Unresolved conflicts will be skipped."):
            self.save_results()
            self.root.destroy()
            print("Application closed by user.")

    def show_conflict(self, index):
        if index >= len(self.conflicts):
            self.root.destroy()
            self.save_results()
            return

        self.current_conflict_index = index
        data = self.conflicts[index]
        
        print(f"Resolving conflict {index+1}/{len(self.conflicts)}: {data['url']} ({data['username']})")
        
        self.lbl_site.config(text=f"Site: {data['url']}")
        self.lbl_user.config(text=f"Username: {data['username']}")
        self.progress_var.set(f"Conflict {index + 1} of {len(self.conflicts)}")
        
        # Clear previous widgets
        for widget in self.compare_frame.winfo_children():
            widget.destroy()
            
        # 1. Show Missing Sources (Context)
        present_sources = set()
        for opt in data['options']:
            for s in opt['sources'].split(", "):
                present_sources.add(s)
        
        missing_sources = self.all_sources - present_sources
        if missing_sources:
            missing_text = ", ".join(missing_sources)
            ttk.Label(self.compare_frame, text=f"Sources with NO entry: {missing_text}", foreground="gray").pack(anchor="w", pady=(0, 10))
            
        # Display Options
        for i, option in enumerate(data['options']):
            color = "blue" if i == 0 else "black"
            f = ttk.LabelFrame(self.compare_frame, text=f"Option {i+1} (Found in: {option['sources']})")
            f.pack(fill=tk.X, pady=5, padx=5)
            
            # Password Entry (Editable)
            entry = ttk.Entry(f, font=("Consolas", 11))
            entry.insert(0, option['password'])
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
            
            # Select Button
            btn = ttk.Button(f, text="Keep This", command=lambda opt=option: self.resolve(opt))
            btn.pack(side=tk.RIGHT, padx=5)
            
        # Skip/Keep Both Button
        ttk.Button(self.compare_frame, text="Skip (Keep All Separate)", command=self.skip_conflict).pack(pady=10)

    def resolve(self, selected_option):
        # Add the winner to resolved data
        conflict = self.conflicts[self.current_conflict_index]
        
        # Calculate losers for notes
        notes = []
        for opt in conflict['options']:
            if opt['password'] != selected_option['password']:
                notes.append(f"[History] {opt['sources']}: {opt['password']}")
        
        final_entry = {
            'url': conflict['url'],
            'username': conflict['username'],
            'password': selected_option['password'],
            'name': conflict['name'],
            'notes': "\n".join(notes)
        }
        self.resolved_data.append(final_entry)
        
        # Next
        self.show_conflict(self.current_conflict_index + 1)

    def skip_conflict(self):
        # Keep all options as separate entries
        conflict = self.conflicts[self.current_conflict_index]
        for opt in conflict['options']:
            self.resolved_data.append({
                'url': conflict['url'],
                'username': conflict['username'],
                'password': opt['password'],
                'name': f"{conflict['name']} ({opt['sources']})",
                'notes': f"Skipped conflict resolution. Source: {opt['sources']}"
            })
        self.show_conflict(self.current_conflict_index + 1)

    def save_results(self):
        if not self.resolved_data:
            print("No data to save.")
            return
            
        df = pd.DataFrame(self.resolved_data)
        
        # Bitwarden Format
        export_df = pd.DataFrame({
            'login_uri': df['url'],
            'login_username': df['username'],
            'login_password': df['password'],
            'name': df['name'],
            'notes': df.get('notes', '')
        })
        
        out_path = os.path.join(self.output_dir, OUTPUT_FILENAME)
        export_df.to_csv(out_path, index=False)
        print(f"SAVED: {out_path}")
        messagebox.showinfo("Success", f"Migration Complete!\nSaved to: {out_path}\n\nTotal Logins: {len(export_df)}")

if __name__ == "__main__":
    app = PasswordMergerApp()
    app.run()
