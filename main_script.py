import os
import tkinter as tk
from tkinter import filedialog
from tkinter import scrolledtext
from tkinter import ttk
import pandas as pd
import ruamel.yaml
from gui_interface import start_gui

def select_directory(title):
    """Prompt user to select a directory."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    folder_selected = filedialog.askdirectory(title=title)
    return folder_selected

def load_yml_file(yml_file_path):
    """Load a YAML file and return the data."""
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
    """Save data to a YAML file."""
    print(f"Saving YAML file: {yml_file_path}")
    yaml = ruamel.yaml.YAML()
    yaml.default_flow_style = False
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.width = 4096
    with open(yml_file_path, 'w', encoding='utf-8') as file:
        yaml.dump(data, file)

def load_csv_file(csv_file_path):
    """Load a CSV file and return a DataFrame."""
    print(f"Loading CSV file: {csv_file_path}")
    df = pd.read_csv(csv_file_path, sep=';')
    return df

def extract_phrases_from_yml(yml_data):
    """Extract phrases from YAML data."""
    phrases = []

    def extract(data):
        if isinstance(data, dict):
            for key, value in data.items():
                extract(value)
        elif isinstance(data, list):
            for item in data:
                extract(item)
        elif isinstance(data, str):
            phrases.append(data)

    extract(yml_data)
    return phrases

def extract_phrases_from_csv(csv_data):
    """Extract phrases from the CSV where column 2 is not empty, combining column 1 and column 2."""
    filtered_data = csv_data[csv_data.iloc[:, 1].notna()]  # Filter rows where column 2 is not empty
    phrases = []
    for _, row in filtered_data.iterrows():
        phrase_1 = row.iloc[0]  # Phrase from column 1
        phrase_2 = row.iloc[1]  # Phrase from column 2
        if pd.notna(phrase_1) and pd.notna(phrase_2):
            combined_phrase = f"{phrase_1} ## {phrase_2}"
            phrases.append(combined_phrase)
    return phrases

def update_phrases_in_txt(txt_file_path, csv_data):
    """Update phrases in a text file based on CSV data."""
    print(f"Updating text file: {txt_file_path}")
    with open(txt_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    filtered_csv_data = csv_data[csv_data.iloc[:, 1].notna()]
    csv_dict = {row[0]: row[1] for row in filtered_csv_data.itertuples(index=False)}
    
    for phrase, replacement in csv_dict.items():
        content = content.replace(phrase, replacement)
    
    with open(txt_file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def save_phrases_to_file(phrases, file_path):
    """Save a list of phrases to a file."""
    with open(file_path, 'w', encoding='utf-8') as file:
        for phrase in phrases:
            file.write(f"{phrase}\n")

def delete_temp_files(file_paths):
    """Delete temporary files."""
    for file_path in file_paths:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted temporary file: {file_path}")

def remove_unused_files(output_dir, processed_files):
    """Remove files in the output directory that are not in the processed_files list."""
    for root_dir, _, files in os.walk(output_dir):
        for file in files:
            file_path = os.path.join(root_dir, file)
            if file_path not in processed_files:
                os.remove(file_path)
                print(f"Deleted unused file: {file_path}")

def process_files(yml_dir, csv_dir, output_dir, progress_var, root):
    print("Processing files...")
    total_files = sum([len(files) for _, _, files in os.walk(yml_dir) if any(file.endswith('.yml') for file in files)])
    processed_files = []
    temp_files = []

    # Create a set to keep track of all files processed
    processed_files_set = set()
    
    for root_dir, _, files in os.walk(yml_dir):
        for file in files:
            if file.endswith('.yml'):
                yml_path = os.path.join(root_dir, file)
                csv_path = os.path.join(csv_dir, os.path.relpath(yml_path, yml_dir).replace('.yml', '.csv'))

                if os.path.exists(csv_path):
                    print(f"Processing file: {yml_path}")

                    try:
                        # Convert .yml to .txt for processing
                        txt_path = os.path.join(root_dir, file.replace('.yml', '.txt'))
                        yml_data = load_yml_file(yml_path)
                        csv_data = load_csv_file(csv_path)

                        # Extract and save phrases from YAML and CSV
                        yml_phrases = extract_phrases_from_yml(yml_data)
                        csv_phrases = extract_phrases_from_csv(csv_data)

                        txt_path_yml = os.path.join(output_dir, f"{os.path.splitext(file)[0]}_yml_phrases.txt")
                        txt_path_csv = os.path.join(output_dir, f"{os.path.splitext(file)[0]}_csv_phrases.txt")

                        save_phrases_to_file(yml_phrases, txt_path_yml)
                        save_phrases_to_file(csv_phrases, txt_path_csv)

                        print(f"Phrases extracted and saved: {txt_path_yml}, {txt_path_csv}")

                        # Save original YAML content to txt file
                        save_yml_file(yml_data, txt_path)
                        temp_files.append(txt_path)  # Keep track of temporary files

                        # Update the text file with CSV data
                        update_phrases_in_txt(txt_path, csv_data)

                        # Create the output path preserving the structure of the original directory
                        relative_path = os.path.relpath(yml_path, yml_dir)
                        output_path = os.path.join(output_dir, relative_path)
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)

                        # Replace the old YAML file with the updated one
                        if os.path.exists(output_path):
                            os.remove(output_path)
                        os.rename(txt_path, output_path)
                        processed_files_set.add(output_path)
                        print(f"Updated YAML file saved to: {output_path}")

                    except Exception as e:
                        print(f"Error processing {yml_path}: {e}")

                    processed_files.append(output_path)
                    progress_var.set((len(processed_files) / total_files) * 100)
                    root.update_idletasks()
                else:
                    print(f"The corresponding CSV file was not found for: {yml_path}")

    tk.Label(root, text="Processing complete!").pack(pady=10)
    root.update_idletasks()

    # Clean up temporary files
    delete_temp_files(temp_files)

    # Remove unused files from the output directory
    remove_unused_files(output_dir, processed_files_set)

if __name__ == "__main__":
    start_gui(process_files)
