import os
import tkinter as tk
from tkinter import filedialog, scrolledtext
from tkinter import ttk
from path_manager import save_paths, load_paths
import pandas as pd
import ruamel.yaml
import sys
import io

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
    
    tk.Button(root, text="Show Logs", command=lambda: log_text.pack(pady=10)).pack(pady=5)

    # Add a "Quit" button to manually close the application
    tk.Button(root, text="Quit", command=root.quit).pack(pady=20)
    
    root.mainloop()

def select_directory(title):
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    folder_selected = filedialog.askdirectory(title=title)
    return folder_selected

def load_yml_file(yml_file_path):
    print(f"Loading YAML file: {yml_file_path}")
    yaml = ruamel.yaml.YAML()
    yaml.default_flow_style = False
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.width = 4096
    with open(yml_file_path, 'r', encoding='utf-8') as file:
        data = yaml.load(file)
        if isinstance(data, dict):
            data = {key if isinstance(key, int) else str(key): value for key, value in data.items()}
        return data

def save_yml_file(data, yml_file_path):
    print(f"Saving YAML file: {yml_file_path}")
    yaml = ruamel.yaml.YAML()
    yaml.default_flow_style = False
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.width = 4096
    with open(yml_file_path, 'w', encoding='utf-8') as file:
        yaml.dump(data, file)

def load_csv_file(csv_file_path):
    print(f"Loading CSV file: {csv_file_path}")
    df = pd.read_csv(csv_file_path, sep=';')
    return df

def update_phrases(yml_data, csv_data):
    print(f"Updating phrases...")
    if csv_data.shape[1] < 2:
        raise ValueError("The CSV file must contain at least two columns.")
    
    csv_dict = {row[0]: row[1] for row in csv_data.itertuples(index=False) if pd.notna(row[1])}

    def replace_phrases(data):
        if isinstance(data, dict):
            return {key: replace_phrases(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [replace_phrases(item) for item in data]
        elif isinstance(data, str):
            if data in csv_dict:
                replacement = csv_dict[data]
                if replacement and replacement != data:
                    return replacement
            return data
        return data

    return replace_phrases(yml_data)

def process_files(yml_dir, csv_dir, output_dir, progress_var, root):
    print("Processing files...")
    total_files = sum([len(files) for _, _, files in os.walk(yml_dir) if any(file.endswith('.yml') for file in files)])
    processed_files = 0
    
    for root_dir, _, files in os.walk(yml_dir):
        for file in files:
            if file.endswith('.yml'):
                yml_path = os.path.join(root_dir, file)
                csv_path = os.path.join(csv_dir, os.path.relpath(yml_path, yml_dir).replace('.yml', '.csv'))

                if os.path.exists(csv_path):
                    print(f"Processing file: {yml_path}")
                    
                    try:
                        yml_data = load_yml_file(yml_path)
                        csv_data = load_csv_file(csv_path)
                        updated_yml_data = update_phrases(yml_data, csv_data)
                        
                        output_path = os.path.join(output_dir, os.path.relpath(yml_path, yml_dir))
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        save_yml_file(updated_yml_data, output_path)
                        print(f"Updated file saved to: {output_path}")
                    except Exception as e:
                        print(f"Error processing {yml_path}: {e}")
                    
                    processed_files += 1
                    progress_var.set((processed_files / total_files) * 100)
                    root.update_idletasks()
                else:
                    print(f"The corresponding CSV file was not found for: {yml_path}")

    tk.Label(root, text="Processing complete!").pack(pady=10)
    root.update_idletasks()

if __name__ == "__main__":
    start_gui(process_files)
