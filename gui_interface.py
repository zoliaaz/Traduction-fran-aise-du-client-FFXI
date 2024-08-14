import os
import tkinter as tk
from tkinter import filedialog, scrolledtext
from tkinter import ttk
import sys
import io
from path_manager import load_paths, save_paths
import webbrowser

class RedirectText(io.StringIO):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.insert(tk.END, message)
        self.text_widget.yview(tk.END)

def select_directory(title):
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    folder_selected = filedialog.askdirectory(title=title)
    return folder_selected

def open_link(event):
    webbrowser.open("https://github.com/zoliaaz/FFXI-fussionner_de_traduction")

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
    frame = tk.Frame(root)
    frame.pack(pady=10, padx=10)

    tk.Label(frame, text="Yml original Directory:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    yml_dir_var = tk.StringVar(value=yml_dir)
    tk.Entry(frame, textvariable=yml_dir_var, width=60).grid(row=0, column=1, padx=5, pady=5)
    tk.Button(frame, text="Browse", command=lambda: yml_dir_var.set(select_directory("Select YAML Directory"))).grid(row=0, column=2, padx=5, pady=5)

    tk.Label(frame, text="CSV with translation Directory:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    csv_dir_var = tk.StringVar(value=csv_dir)
    tk.Entry(frame, textvariable=csv_dir_var, width=60).grid(row=1, column=1, padx=5, pady=5)
    tk.Button(frame, text="Browse", command=lambda: csv_dir_var.set(select_directory("Select CSV Directory"))).grid(row=1, column=2, padx=5, pady=5)

    tk.Label(frame, text="Output Directory:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
    output_dir_var = tk.StringVar(value=output_dir)
    tk.Entry(frame, textvariable=output_dir_var, width=60).grid(row=2, column=1, padx=5, pady=5)
    tk.Button(frame, text="Browse", command=lambda: output_dir_var.set(select_directory("Select Output Directory"))).grid(row=2, column=2, padx=5, pady=5)

    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, length=400)
    progress_bar.pack(pady=10)

    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)

    tk.Button(button_frame, text="Start Processing", command=lambda: start_processing()).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Quit", command=root.quit).pack(side=tk.LEFT, padx=5)

    def start_processing():
        save_paths(yml_dir_var.get(), csv_dir_var.get(), output_dir_var.get())
        
        if yml_dir_var.get() and csv_dir_var.get() and output_dir_var.get():
            root.after(100, process_files_callback, yml_dir_var.get(), csv_dir_var.get(), output_dir_var.get(), progress_var, root)
        else:
            tk.Label(root, text="Please select all directories.").pack(pady=10)

    # Add author credits
    tk.Label(root, text="Author: Zoliaaz & ChatGPT - 14/08/2024", anchor="e").pack(side=tk.BOTTOM, pady=5, padx=10, anchor='e')

    # Add clickable link
    link_label = tk.Label(root, text="https://github.com/zoliaaz/FFXI-fussionner_de_traduction", fg="blue", cursor="hand2")
    link_label.pack(side=tk.BOTTOM, pady=5, padx=10, anchor='e')
    link_label.bind("<Button-1>", open_link)

    root.mainloop()
