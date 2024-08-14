import os
import tkinter as tk
from tkinter import filedialog
from tkinter import scrolledtext
from tkinter import ttk
from path_manager import save_paths, load_paths
import pandas as pd
import ruamel.yaml
import sys
import io

from gui_interface import start_gui

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
