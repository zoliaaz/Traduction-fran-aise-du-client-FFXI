import os
import tkinter as tk
from tkinter import filedialog
import pandas as pd
import ruamel.yaml
from gui_interface import start_gui
import re

def select_directory(title):
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    folder_selected = filedialog.askdirectory(title=title)
    return folder_selected

def load_yml_file(yml_file_path):
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
    yaml = ruamel.yaml.YAML()
    yaml.default_flow_style = False
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.width = 4096
    with open(yml_file_path, 'w', encoding='utf-8') as file:
        yaml.dump(data, file)

def load_csv_file(csv_file_path):
    df = pd.read_csv(csv_file_path, sep=';')
    return df

def normalize_phrase(phrase):
    """Normalize the phrase by removing dynamic elements and simplifying options."""
    # Remove dynamic elements like ${name-player} or ${choice-player-gender}
    phrase = re.sub(r'\$\{.*?\}', '', phrase)
    # Simplify options like [He's/She's] to a generic form [He's]
    phrase = re.sub(r'\[(.*?)/(.*?)\]', r'\1', phrase)
    # Remove leading/trailing whitespace
    return phrase.strip()

def update_phrases(yml_data, csv_dict):
    def replace_phrases(data, csv_dict):
        if isinstance(data, dict):
            return {key: replace_phrases(value, csv_dict) for key, value in data.items()}
        elif isinstance(data, list):
            return [replace_phrases(item, csv_dict) for item in data]
        elif isinstance(data, str):
            normalized_data = normalize_phrase(data)
            if normalized_data in csv_dict:
                replacement = csv_dict[normalized_data]
                if replacement and replacement != normalized_data:
                    return replacement
            return data
        return data

    return replace_phrases(yml_data, csv_dict)

def log_untranslated_phrases(yml_data, csv_dict, log_file_path):
    untranslated_phrases = set()

    def find_untranslated_phrases(data):
        if isinstance(data, dict):
            for key, value in data.items():
                find_untranslated_phrases(value)
        elif isinstance(data, list):
            for item in data:
                find_untranslated_phrases(item)
        elif isinstance(data, str):
            normalized_data = normalize_phrase(data)
            if normalized_data not in {key.strip().lower() for key in csv_dict.keys()}:
                untranslated_phrases.add(data)  # Add to set instead of writing directly to file

    find_untranslated_phrases(yml_data)

    with open(log_file_path, 'w', encoding='utf-8') as file:
        for phrase in untranslated_phrases:
            file.write(phrase + '\n')

def translate_untranslated_phrases(yml_data, csv_dict):
    def replace_untranslated(data):
        if isinstance(data, dict):
            return {key: replace_untranslated(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [replace_untranslated(item) for item in data]
        elif isinstance(data, str):
            normalized_data = normalize_phrase(data)
            if normalized_data in csv_dict:
                return csv_dict[normalized_data]
            return data
        return data

    return replace_untranslated(yml_data)

def process_files(yml_dir, csv_dir, output_dir, progress_var, root):
    total_files = sum([len(files) for _, _, files in os.walk(yml_dir) if any(file.endswith('.yml') for file in files)])
    processed_files = 0
    
    for root_dir, _, files in os.walk(yml_dir):
        for file in files:
            if file.endswith('.yml'):
                yml_path = os.path.join(root_dir, file)
                csv_path = os.path.join(csv_dir, os.path.relpath(yml_path, yml_dir).replace('.yml', '.csv'))

                if os.path.exists(csv_path):
                    try:
                        yml_data = load_yml_file(yml_path)
                        csv_data = load_csv_file(csv_path)
                        csv_dict = {normalize_phrase(row[0].strip()): row[1].strip() for row in csv_data.itertuples(index=False) if pd.notna(row[1])}

                        # Update phrases using CSV
                        updated_yml_data = update_phrases(yml_data, csv_dict)
                        
                        # Log untranslated phrases
                        untranslated_log_path = os.path.join(output_dir, 'untranslated_phrases.txt')
                        log_untranslated_phrases(updated_yml_data, csv_dict, untranslated_log_path)

                        # Attempt to replace untranslated phrases with translations
                        translated_yml_data = translate_untranslated_phrases(updated_yml_data, csv_dict)
                        
                        output_path = os.path.join(output_dir, os.path.relpath(yml_path, yml_dir))
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        save_yml_file(translated_yml_data, output_path)
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
