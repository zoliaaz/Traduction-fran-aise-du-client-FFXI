import os
import pandas as pd
import sqlite3
from deep_translator import GoogleTranslator
from tkinter import Tk, Button, messagebox, IntVar, Checkbutton
from tkinter.filedialog import askdirectory, askopenfilename
import re
import threading
import time
import json
import sys

# Initialiser le traducteur
translator = GoogleTranslator(source='en', target='fr')

# Variables de contrôle pour arrêter la traduction et sauvegarder les fichiers
stop_translation = False
resume_info = {}
processed_files = set()
translate_from_db_only = False

def get_db_path():
    if getattr(sys, 'frozen', False):  # Si l'application est exécutée à partir d'un fichier .exe
        return os.path.join(sys._MEIPASS, 'translations.db')
    else:  # Sinon, exécuter en mode développement
        return os.path.join(os.path.dirname(__file__), 'translations.db')

def get_status_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'translation_status.json')
    else:
        return os.path.join(os.path.dirname(__file__), 'translation_status.json')

DB_PATH = get_db_path()
STATUS_FILE = get_status_path()

def create_translation_db(db_path=DB_PATH):
    db_directory = os.path.dirname(db_path)
    if not os.path.exists(db_directory):
        os.makedirs(db_directory)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS translations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phrase_en TEXT UNIQUE,
                phrase_fr TEXT
            )
        ''')
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")

def import_existing_translations(csv_file, db_path=DB_PATH):
    create_translation_db(db_path)  # Assurer que la base de données existe
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    df = pd.read_csv(csv_file, delimiter=';', quotechar='"', escapechar='\\')
    
    # Assurez-vous que les colonnes existent dans le CSV
    if 'Phrase en Anglais' not in df.columns or 'Phrase en Français' not in df.columns:
        print('Required columns not found in the common phrases file.')
        conn.close()
        return

    for _, row in df.iterrows():
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO translations (phrase_en, phrase_fr) VALUES (?, ?)
            ''', (row['Phrase en Anglais'], row['Phrase en Français']))
        except sqlite3.Error as e:
            print(f"SQLite error while importing: {e}")
    
    conn.commit()
    conn.close()

def load_resume_info():
    global resume_info, processed_files
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r') as f:
                data = json.load(f)
                resume_info = data.get('resume_info', {})
                processed_files = set(data.get('processed_files', []))
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading resume info: {e}")
            resume_info = {}
            processed_files = set()
    else:
        resume_info = {}
        processed_files = set()

def save_resume_info():
    global resume_info, processed_files
    try:
        with open(STATUS_FILE, 'w') as f:
            json.dump({
                'resume_info': resume_info,
                'processed_files': list(processed_files)
            }, f, indent=4)
    except IOError as e:
        print(f"Error saving resume info: {e}")

def fetch_translation_from_db(text, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT phrase_fr FROM translations WHERE phrase_en = ?', (text,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def translate_text(text, row_num=None):
    if translate_from_db_only:
        db_translation = fetch_translation_from_db(text)
        if db_translation:
            print(f"Row {row_num}: Phrase retrieved from database.")
            return db_translation
        else:
            print(f"Row {row_num}: Phrase not found in database, skipping translation.")
            return ''  # Return empty if not found in database

    db_translation = fetch_translation_from_db(text)
    if db_translation:
        print(f"Row {row_num}: Phrase retrieved from database.")
        return db_translation

    pattern = re.compile(r'\$\{[^}]*\}|\[\w*\]|\$\w*\$')
    parts = pattern.split(text)
    separators = pattern.findall(text)

    translated_parts = []
    for part in parts:
        if part.strip():
            try:
                translation = translator.translate(part)
                if translation:
                    translation = translation.replace('"', '“').replace('"', '”')
                    translation = translation.replace('\xa0', ' ')
                    translated_parts.append(translation)
                else:
                    translated_parts.append('')
            except Exception as e:
                print(f"Error translating text '{part}': {e}")
                translated_parts.append('')
        else:
            translated_parts.append('')

    translated_text = ''.join([p + s for p, s in zip(translated_parts, separators + [''])])
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO translations (phrase_en, phrase_fr) VALUES (?, ?)
    ''', (text, translated_text))
    conn.commit()
    conn.close()
    
    print(f"Row {row_num}: Phrase translated using Google Translator.")
    return translated_text if translated_text.strip() else ''

def process_csv_file(filepath, delimiter=';'):
    global stop_translation, resume_info
    print(f'Processing file: {filepath}')

    output_filepath = filepath.replace('.csv', '_translated.csv')

    if not os.path.exists(output_filepath):
        print(f'File does not exist, starting translation from the beginning: {output_filepath}')
        start_row = 0
        df_translated = None
    else:
        start_row = resume_info.get(filepath, 0)
        df_translated = pd.read_csv(output_filepath, delimiter=delimiter)
        print(f'Resuming translation from row {start_row}')

    try:
        df = pd.read_csv(filepath, delimiter=delimiter, quotechar='"', escapechar='\\', on_bad_lines='skip')
    except pd.errors.ParserError as e:
        print(f"ParserError reading {filepath}: {e}")
        return
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return

    print(f'Columns found: {df.columns.tolist()}')

    if 'Phrase en Anglais' not in df.columns or 'Phrase en Français' not in df.columns:
        print('Columns not found. Skipping file.')
        return

    df['Phrase en Français'] = df['Phrase en Français'].astype(str)

    if df_translated is not None:
        df.update(df_translated)
    
    total_rows = len(df)
    start_time = time.time()

    try:
        print("Starting translation...")
        for index in range(start_row, total_rows):
            if stop_translation:
                resume_info[filepath] = index
                save_partial_csv(df, output_filepath, delimiter)
                save_resume_info()
                return

            row = df.iloc[index]
            phrase_en = row['Phrase en Anglais']
            phrase_fr = row['Phrase en Français']

            # Traduire uniquement si la case contient "nan"
            if pd.isna(phrase_fr) or phrase_fr.strip().lower() == "nan":
                elapsed_time = time.time() - start_time
                processed_rows = index + 1
                progress_percentage = (processed_rows / total_rows) * 100
                estimated_total_time = (elapsed_time / processed_rows) * total_rows if processed_rows > 0 else 0
                remaining_time = estimated_total_time - elapsed_time

                print(f"Translating row {index + 1}/{total_rows} ({progress_percentage:.2f}%) - Estimated time remaining: {remaining_time // 60:.0f}m {remaining_time % 60:.0f}s")
                
                df.at[index, 'Phrase en Français'] = translate_text(phrase_en, row_num=index + 1)
            else:
                print(f"Row {index + 1}: Phrase already translated or marked.")

        if not stop_translation:
            print("Translation completed.")
            processed_files.add(filepath)
            resume_info.pop(filepath, None)
            save_partial_csv(df, output_filepath, delimiter)
        else:
            print("Translation stopped.")
        
    except Exception as e:
        print(f"Error applying translation: {e}")
        return

def save_partial_csv(df, output_filepath, delimiter=';'):
    try:
        df.to_csv(output_filepath, sep=delimiter, index=False)
        print(f'Saved translated file to: {output_filepath}')
    except Exception as e:
        print(f"Error saving file {output_filepath}: {e}")

def process_directory(directory, delimiter=';'):
    global stop_translation
    for root, dirs, files in os.walk(directory):
        if stop_translation:
            break
        for file in files:
            if stop_translation:
                break
            if file.endswith('.csv'):
                file_path = os.path.join(root, file)
                if file_path not in processed_files:
                    print(f'Found file: {file}')
                    process_csv_file(file_path, delimiter)
        if stop_translation:
            break

def select_directory():
    root = Tk()
    root.withdraw()
    directory = askdirectory(title="Select Directory with CSV Files")
    return directory

def select_file_for_db_update():
    root = Tk()
    root.withdraw()
    file_path = askopenfilename(title="Select CSV File to Add Phrases", filetypes=[("CSV files", "*.csv")])
    return file_path

def start_translation():
    global stop_translation
    global translate_from_db_only
    stop_translation = False
    load_resume_info()
    create_translation_db(DB_PATH)

    root_directory = select_directory()

    if root_directory:
        print(f"Selected directory: {root_directory}")

        translation_thread = threading.Thread(target=process_directory, args=(root_directory,))
        translation_thread.start()
    else:
        print("No directory selected.")

def add_phrases_to_db():
    create_translation_db(DB_PATH)  # Assurer que la base de données existe
    csv_file = select_file_for_db_update()

    if csv_file:
        import_existing_translations(csv_file, DB_PATH)
        print(f"Imported phrases from: {csv_file}")
    else:
        print("No file selected for import.")

def show_help():
    messagebox.showinfo("CSV Format Help", 
        "The CSV file to add phrases to the database must have the following columns:\n\n"
        "1. Phrase en Anglais: The English phrase to be translated.\n"
        "2. Phrase en Français: The corresponding French translation.\n\n"
        "The file should be saved in CSV format with ';' as the delimiter.")

def stop_translation_process():
    global stop_translation
    stop_translation = True
    messagebox.showinfo("Translation Stopped", "Translation process has been stopped. The partially translated files have been saved.")

def resume_translation():
    global stop_translation
    global translate_from_db_only
    stop_translation = False
    load_resume_info()  # Charger les informations de reprise
    
    root_directory = os.path.dirname(next(iter(resume_info.keys()), ''))

    if root_directory:
        print(f"Resuming directory: {root_directory}")

        translation_thread = threading.Thread(target=process_directory, args=(root_directory,))
        translation_thread.start()
    else:
        print("No directory selected or found.")

def set_translate_mode():
    global translate_from_db_only
    translate_from_db_only = not translate_from_db_only
    mode = "only from DB" if translate_from_db_only else "full translation"
    print(f"Translation mode set to: {mode}")

app = Tk()
app.title("CSV Translation Tool")

start_button = Button(app, text="Start Translation", command=start_translation)
start_button.pack(pady=10)

stop_button = Button(app, text="Stop Translation", command=stop_translation_process)
stop_button.pack(pady=10)

resume_button = Button(app, text="Resume Translation", command=resume_translation)
resume_button.pack(pady=10)

add_phrases_button = Button(app, text="Add Phrases to DB", command=add_phrases_to_db)
add_phrases_button.pack(pady=10)

help_button = Button(app, text="Help", command=show_help)
help_button.pack(pady=10)

# Ajout du bouton pour activer/désactiver le mode traduction uniquement à partir de la base de données
translate_mode_var = IntVar()
translate_mode_checkbox = Checkbutton(app, text="Translate only from DB", variable=translate_mode_var, command=set_translate_mode)
translate_mode_checkbox.pack(pady=10)

app.mainloop()
