import os
import tkinter as tk
from tkinter import filedialog, scrolledtext
from tkinter import ttk
import pandas as pd
import ruamel.yaml
import io
import sys
from path_manager import load_paths, save_paths

class RedirectText(io.StringIO):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.insert(tk.END, message)
        self.text_widget.yview(tk.END)

def start_gui(process_files_callback):
    root = tk.Tk()
    root.title("YAML and CSV File Processing")

    # Create a ScrolledText widget to show logs
    log_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=15, width=80)
    log_text.pack(pady=10)

    # Redirect stdout and stderr to the ScrolledText widget
    sys.stdout = RedirectText(log_text)
    sys.stderr = RedirectText(log_text)

    # Load previously saved paths if they exist
    paths = load_paths()
    if paths:
        yml_dir = paths.get('yml_dir', '')
        csv_dir = paths.get('csv_dir', '')
        output_dir = paths.get('output_dir', '')
    else:
        yml_dir = ''
        csv_dir = ''
        output_dir = ''

    # User interface
    tk.Label(root, text="Please select the directory containing YAML files...").pack(pady=10)
    yml_dir_var = tk.StringVar(value=yml_dir)
    tk.Entry(root, textvariable=yml_dir_var, width=60).pack(pady=5)
    tk.Button(root, text="Browse", command=lambda: yml_dir_var.set(select_directory("Select YAML Directory"))).pack(pady=5)

    tk.Label(root, text="Please select the directory containing CSV files...").pack(pady=10)
    csv_dir_var = tk.StringVar(value=csv_dir)
    tk.Entry(root, textvariable=csv_dir_var, width=60).pack(pady=5)
    tk.Button(root, text="Browse", command=lambda: csv_dir_var.set(select_directory("Select CSV Directory"))).pack(pady=5)

    tk.Label(root, text="Please select the output directory for modified YAML files...").pack(pady=10)
    output_dir_var = tk.StringVar(value=output_dir)
    tk.Entry(root, textvariable=output_dir_var, width=60).pack(pady=5)
    tk.Button(root, text="Browse", command=lambda: output_dir_var.set(select_directory("Select Output Directory"))).pack(pady=5)

    tk.Label(root, text="Processing in progress...").pack(pady=10)

    # Progress bar
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, length=400)
    progress_bar.pack(pady=20)

    def start_processing():
        save_paths(yml_dir_var.get(), csv_dir_var.get(), output_dir_var.get())
        
        if yml_dir_var.get() and csv_dir_var.get() and output_dir_var.get():
            root.after(100, process_files_callback, yml_dir_var.get(), csv_dir_var.get(), output_dir_var.get(), progress_var, root)
        else:
            tk.Label(root, text="Please select all directories.").pack(pady=10)

    tk.Button(root, text="Start Processing", command=start_processing).pack(pady=20)
    
  
    tk.Button(root, text="Quit", command=root.quit).pack(pady=20)
    
    root.mainloop()

def select_directory(title):
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    folder_selected = filedialog.askdirectory(title=title)
    return folder_selected
