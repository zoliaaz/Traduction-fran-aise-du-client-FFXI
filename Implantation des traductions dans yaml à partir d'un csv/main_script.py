import os
import tkinter as tk
from tkinter import filedialog
from tkinter import scrolledtext
from tkinter import ttk
import pandas as pd
import ruamel.yaml
from gui_interface import start_gui

def select_directory(title):
    """Demande à l'utilisateur de sélectionner un répertoire."""
    root = tk.Tk()
    root.withdraw()  # Masquer la fenêtre principale
    folder_selected = filedialog.askdirectory(title=title)
    return folder_selected

def load_yml_file(yml_file_path):
    """Charge un fichier YAML et retourne les données."""
    print(f"Chargement du fichier YAML : {yml_file_path}")
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
    """Sauvegarde les données dans un fichier YAML."""
    print(f"Enregistrement du fichier YAML : {yml_file_path}")
    yaml = ruamel.yaml.YAML()
    yaml.default_flow_style = False
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.width = 4096
    with open(yml_file_path, 'w', encoding='utf-8') as file:
        yaml.dump(data, file)

def load_csv_file(csv_file_path):
    """Charge un fichier CSV et retourne un DataFrame."""
    print(f"Chargement du fichier CSV : {csv_file_path}")
    df = pd.read_csv(csv_file_path, sep=';')
    return df

def extract_phrases_from_yml(yml_data):
    """Extrait les phrases des données YAML."""
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
    """Extrait les phrases du CSV où la colonne 2 n'est pas vide, combinant colonne 1 et colonne 2."""
    filtered_data = csv_data[csv_data.iloc[:, 1].notna()]  # Filtre les lignes où la colonne 2 n'est pas vide
    phrases = []
    for _, row in filtered_data.iterrows():
        phrase_1 = row.iloc[0]  # Phrase de la colonne 1
        phrase_2 = row.iloc[1]  # Phrase de la colonne 2
        if pd.notna(phrase_1) and pd.notna(phrase_2):  # Utiliser 'and' pour les opérations logiques
            combined_phrase = f"{phrase_1} ## {phrase_2}"
            phrases.append(combined_phrase)
    return phrases

def update_phrases_in_txt(txt_file_path, csv_data):
    """Met à jour les phrases dans un fichier texte en fonction des données du CSV."""
    print(f"Mise à jour du fichier texte : {txt_file_path}")
    with open(txt_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    filtered_csv_data = csv_data[csv_data.iloc[:, 1].notna()]
    csv_dict = {row[0]: row[1] for row in filtered_csv_data.itertuples(index=False)}
    
    for phrase, replacement in csv_dict.items():
        content = content.replace(phrase, replacement)
    
    with open(txt_file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def save_phrases_to_file(phrases, file_path):
    """Sauvegarde une liste de phrases dans un fichier."""
    with open(file_path, 'w', encoding='utf-8') as file:
        for phrase in phrases:
            file.write(f"{phrase}\n")

def delete_temp_files(file_paths):
    """Supprime les fichiers temporaires."""
    for file_path in file_paths:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Fichier temporaire supprimé : {file_path}")

def remove_unused_files(output_dir, processed_files):
    """Supprime les fichiers dans le répertoire de sortie qui ne figurent pas dans la liste des fichiers traités."""
    for root_dir, _, files in os.walk(output_dir):
        for file in files:
            file_path = os.path.join(root_dir, file)
            if file_path not in processed_files and file.endswith('.txt'):  # Supprimer uniquement les fichiers .txt
                os.remove(file_path)
                print(f"Fichier inutilisé supprimé : {file_path}")

def process_files(yml_dir, csv_dir, output_dir, progress_var, root):
    print("Traitement des fichiers...")
    total_files = sum([len(files) for _, _, files in os.walk(yml_dir) if any(file.endswith('.yml') for file in files)])
    processed_files = []
    temp_files = []

    # Créer un ensemble pour suivre tous les fichiers traités
    processed_files_set = set()
    
    for root_dir, _, files in os.walk(yml_dir):
        for file in files:
            if file.endswith('.yml'):
                yml_path = os.path.join(root_dir, file)
                csv_path = os.path.join(csv_dir, os.path.relpath(yml_path, yml_dir).replace('.yml', '.csv'))

                if os.path.exists(csv_path):
                    print(f"Traitement du fichier : {yml_path}")

                    try:
                        # Convertir .yml en .txt pour le traitement
                        txt_path = os.path.join(root_dir, file.replace('.yml', '.txt'))
                        yml_data = load_yml_file(yml_path)
                        csv_data = load_csv_file(csv_path)

                        # Extraire et sauvegarder les phrases depuis YAML et CSV
                        yml_phrases = extract_phrases_from_yml(yml_data)
                        csv_phrases = extract_phrases_from_csv(csv_data)

                        txt_path_yml = os.path.join(output_dir, f"{os.path.splitext(file)[0]}_yml_phrases.txt")
                        txt_path_csv = os.path.join(output_dir, f"{os.path.splitext(file)[0]}_csv_phrases.txt")

                        save_phrases_to_file(yml_phrases, txt_path_yml)
                        save_phrases_to_file(csv_phrases, txt_path_csv)

                        print(f"Phrases extraites et sauvegardées : {txt_path_yml}, {txt_path_csv}")

                        # Sauvegarder le contenu YAML original dans un fichier texte
                        save_yml_file(yml_data, txt_path)
                        temp_files.append(txt_path)  # Garder une trace des fichiers temporaires

                        # Mettre à jour le fichier texte avec les données CSV
                        update_phrases_in_txt(txt_path, csv_data)

                        # Créer le chemin de sortie en préservant la structure du répertoire original
                        relative_path = os.path.relpath(yml_path, yml_dir)
                        output_path = os.path.join(output_dir, relative_path)
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)

                        # Remplacer l'ancien fichier YAML par le nouveau
                        if os.path.exists(output_path):
                            os.remove(output_path)
                        os.rename(txt_path, output_path)
                        processed_files_set.add(output_path)
                        print(f"Fichier YAML mis à jour enregistré : {output_path}")

                    except Exception as e:
                        print(f"Erreur lors du traitement de {yml_path} : {e}")

                    processed_files.append(output_path)
                    progress_var.set((len(processed_files) / total_files) * 100)
                    root.update_idletasks()
                else:
                    print(f"Le fichier CSV correspondant n'a pas été trouvé pour : {yml_path}")

    tk.Label(root, text="Traitement terminé !").pack(pady=10)
    root.update_idletasks()

    # Nettoyer les fichiers temporaires
    delete_temp_files(temp_files)

    # Supprimer les fichiers inutilisés dans le répertoire de sortie
    remove_unused_files(output_dir, processed_files_set)

if __name__ == "__main__":
    start_gui(process_files)
