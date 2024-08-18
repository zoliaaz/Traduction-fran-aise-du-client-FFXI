import os
import yaml
import pandas as pd
import tkinter as tk
from tkinter import filedialog
from datetime import datetime

def load_yaml(file_path):
    """Charge le fichier YAML en ignorant les sections avec des erreurs, autant que possible, et calcule le pourcentage de données extraites."""
    data = {}
    total_lines = 0
    valid_lines = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            total_lines = len(lines)
            valid_yaml = ""
            for line in lines:
                try:
                    yaml.safe_load(line)  # Essayez de charger chaque ligne individuellement
                    valid_yaml += line
                    valid_lines += 1
                except yaml.YAMLError:
                    continue  # Ignorer la ligne en cas d'erreur
            data = yaml.safe_load(valid_yaml)
    except Exception as e:
        print(f"Erreur lors du chargement du fichier {file_path}: {e}")

    extraction_percentage = (valid_lines / total_lines) * 100 if total_lines > 0 else 0
    print(f"Extraction réussie à {extraction_percentage:.2f}% pour le fichier : {file_path}")

    return data or {}

def extract_phrases(data):
    """Extrait les phrases des données YAML en utilisant les valeurs, en tenant compte des lignes séparées."""
    phrases = []
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, str):
                phrases.extend(value.split('\n'))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        phrases.extend(item.split('\n'))
            elif isinstance(value, dict):
                nested_phrases = extract_phrases(value)
                phrases.extend(nested_phrases)
    return [phrase.strip() for phrase in phrases if phrase.strip()]

def load_previous_yaml(file_path):
    """Charge l'ancien contenu YAML s'il existe."""
    previous_yaml_path = file_path + ".old"
    if os.path.exists(previous_yaml_path):
        return load_yaml(previous_yaml_path)
    return {}

def save_current_yaml(file_path, data):
    """Sauvegarde le contenu YAML actuel pour référence future."""
    previous_yaml_path = file_path + ".old"
    with open(previous_yaml_path, 'w', encoding='utf-8') as file:
        yaml.dump(data, file, allow_unicode=True)

def save_phrases_to_csv(english_phrases, french_phrases, file_path, new_content=False):
    """Sauvegarde les phrases anglaises et françaises dans un fichier CSV."""
    try:
        # Charger les phrases existantes s'il y a lieu
        if os.path.exists(file_path):
            existing_df = pd.read_csv(file_path, sep=';', encoding='utf-8')
            existing_english_phrases = existing_df['Phrase en Anglais'].tolist()
            existing_french_phrases = existing_df['Phrase en Français'].tolist()
        else:
            existing_english_phrases = []
            existing_french_phrases = []

        # Ajouter une séparation pour le nouveau contenu si nécessaire
        if os.path.exists(file_path) and new_content:
            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            separator = [f"--- Nouveau contenu ajouté le {current_date} ---"]
            all_english_phrases = existing_english_phrases + separator + english_phrases
            all_french_phrases = existing_french_phrases + [''] + french_phrases  # Ajouter une ligne vide pour le séparateur
        else:
            all_english_phrases = existing_english_phrases + english_phrases
            all_french_phrases = existing_french_phrases + french_phrases

        # Égaliser la longueur des listes
        max_length = max(len(all_english_phrases), len(all_french_phrases))
        all_english_phrases.extend([''] * (max_length - len(all_english_phrases)))
        all_french_phrases.extend([''] * (max_length - len(all_french_phrases)))

        # Sauvegarder dans le fichier CSV
        df = pd.DataFrame({
            'Phrase en Anglais': all_english_phrases,
            'Phrase en Français': all_french_phrases
        })
        df.to_csv(file_path, index=False, sep=';', encoding='utf-8')
        print(f"Phrases sauvegardées dans : {file_path}")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde dans le fichier CSV : {e}")




def select_directory(title):
    """Ouvre une boîte de dialogue pour sélectionner un répertoire."""
    root = tk.Tk()
    root.withdraw()
    return filedialog.askdirectory(title=title)

def process_directories(english_dir, french_dir, output_dir, only_english=False):
    """Extrait les phrases des fichiers YAML anglais et français, ou seulement anglais, et crée des fichiers CSV pour chaque paire de fichiers."""
    for root, _, files in os.walk(english_dir):
        for file in files:
            if file.endswith('.yml'):
                english_file = os.path.join(root, file)
                
                # Si on est en mode "only_english", ignorer le dossier français
                if only_english:
                    french_file = None
                else:
                    french_file = os.path.join(french_dir, os.path.relpath(english_file, english_dir))
                    if not os.path.exists(french_file):
                        print(f"Fichier correspondant introuvable pour : {english_file}")
                        continue

                relative_path = os.path.relpath(english_file, english_dir)
                output_file_dir = os.path.join(output_dir, os.path.dirname(relative_path))
                output_file = os.path.join(output_file_dir, f"{os.path.splitext(file)[0]}.csv")

                if not os.path.exists(output_file_dir):
                    os.makedirs(output_file_dir)

                print(f"Traitement de : {english_file}")
                if french_file:
                    print(f"et {french_file}")

                try:
                    # Charger les données YAML actuelles et précédentes
                    english_data = load_yaml(english_file)
                    previous_english_data = load_previous_yaml(english_file)

                    # Extraire les phrases
                    english_phrases = extract_phrases(english_data)
                    previous_english_phrases = extract_phrases(previous_english_data)

                    # Comparer et trouver les nouvelles phrases
                    new_english_phrases = [phrase for phrase in english_phrases if phrase not in previous_english_phrases]

                    # En mode "only_english", on ne remplit que les colonnes anglaises
                    if only_english:
                        new_french_phrases = ['' for _ in new_english_phrases]
                    else:
                        # En mode normal, on extrait aussi les phrases françaises
                        french_data = load_yaml(french_file)
                        french_phrases = extract_phrases(french_data)
                        
                        # Associer chaque phrase anglaise à une phrase française correspondante
                        # Ici, nous supposons que les phrases sont alignées et ont la même longueur
                        max_length = max(len(new_english_phrases), len(french_phrases))
                        new_french_phrases = french_phrases[:max_length]
                        
                        # Ajouter des lignes vides si nécessaire
                        if len(new_french_phrases) < len(new_english_phrases):
                            new_french_phrases.extend([''] * (len(new_english_phrases) - len(new_french_phrases)))

                    # Déterminer si un fichier .old existe pour décider d'ajouter ou non le séparateur
                    new_content = os.path.exists(english_file + ".old")

                    # Sauvegarder les nouvelles phrases à la fin du CSV
                    save_phrases_to_csv(new_english_phrases, new_french_phrases, output_file, new_content=new_content)

                    # Sauvegarder l'état actuel du fichier YAML
                    save_current_yaml(english_file, english_data)

                except Exception as e:
                    print(f"Erreur lors du traitement du fichier {english_file} : {e}")



def main():
    try:
        print("Début du script")
        
        # Choisir le mode de traitement : uniquement anglais ou anglais/français
        mode_choice = input("Souhaitez-vous traiter uniquement les fichiers anglais ? (o/n) : ").strip().lower()
        only_english = mode_choice == 'o'
        
        print("Veuillez sélectionner les répertoires.")
        english_dir = select_directory("Sélectionnez le répertoire contenant les fichiers YAML en anglais")
        
        # Ne pas demander de répertoire français si on est en mode "only_english"
        french_dir = None
        if not only_english:
            french_dir = select_directory("Sélectionnez le répertoire contenant les fichiers YAML en français")
            
        output_dir = select_directory("Sélectionnez le répertoire pour sauvegarder les fichiers CSV")

        if not english_dir or (not french_dir and not only_english) or not output_dir:
            print("Tous les répertoires doivent être sélectionnés pour continuer.")
            return

        process_directories(english_dir, french_dir, output_dir, only_english=only_english)
        print("Traitement terminé.")
        input("Appuyez sur Entrée pour fermer...")
    except Exception as e:
        print(f"Erreur générale : {e}")
        input("Appuyez sur Entrée pour fermer...")


if __name__ == "__main__":
    main()
