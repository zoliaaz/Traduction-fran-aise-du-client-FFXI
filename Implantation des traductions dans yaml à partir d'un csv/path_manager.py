import os
import json

def save_paths(yml_dir, csv_dir, output_dir):
    """
    Save the paths to a JSON file in the same directory as the script.
    """
    paths = {
        'yml_dir': yml_dir,
        'csv_dir': csv_dir,
        'output_dir': output_dir
    }
    
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create the full path for paths_config.json in the script directory
    file_path = os.path.join(script_dir, 'paths_config.json')
    
    print(f"Attempting to save to: {file_path}")
    print(f"Paths to save: {paths}")
    
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(paths, file, ensure_ascii=False, indent=4)
        print(f"Paths successfully saved to {file_path}")
    except PermissionError as e:
        print(f"Permission Error: {e}")
    except Exception as e:
        print(f"Error saving paths: {e}")

def load_paths():
    """
    Load the paths from the JSON file in the same directory as the script.
    """
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create the full path for paths_config.json in the script directory
    file_path = os.path.join(script_dir, 'paths_config.json')
    
    print(f"Attempting to load from: {file_path}")
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                print(f"Paths loaded: {data}")
                return data
        except Exception as e:
            print(f"Error loading paths: {e}")
    else:
        print(f"File does not exist: {file_path}")
    return None
