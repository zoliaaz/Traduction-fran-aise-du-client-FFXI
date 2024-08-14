import os
import yaml
import pandas as pd
import tkinter as tk
from tkinter import filedialog

def load_yaml(file_path):
    """Charge le fichier YAML et retourne les données."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            return data
    except Exception as e:
        print(f"Erreur lors du chargement du fichier {file_path}: {e}")
        return {}

def extract_phrases(data):
    """Extrait les phrases des données YAML en utilisant les valeurs, en tenant compte des lignes séparées."""
    phrases = []
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, str):
                # Si le texte contient des sauts de ligne, divisez-le en plusieurs lignes
                phrases.extend(value.split('\n'))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        phrases.extend(item.split('\n'))
            elif isinstance(value, dict):
                nested_phrases = extract_phrases(value)
                phrases.extend(nested_phrases)
    return [phrase.strip() for phrase in phrases if phrase.strip()]  # Nettoyage des espaces vides

def save_phrases_to_csv(english_phrases, french_phrases, file_path):
    """Sauvegarde les phrases anglaises et françaises dans un fichier CSV."""
    try:
        max_len = max(len(english_phrases), len(french_phrases))
        # S'assurer que les deux listes ont la même longueur
        english_phrases.extend([""] * (max_len - len(english_phrases)))
        french_phrases.extend([""] * (max_len - len(french_phrases)))

        # Créer un DataFrame avec des lignes alignées
        df = pd.DataFrame({
            'Phrase en Anglais': english_phrases,
            'Phrase en Français': french_phrases
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

def process_directories(english_dir, french_dir, output_dir):
    """Extrait les phrases des fichiers YAML anglais et français et crée des fichiers CSV pour chaque paire de fichiers."""
    for root, _, files in os.walk(english_dir):
        for file in files:
            if file.endswith('.yml'):
                english_file = os.path.join(root, file)
                french_file = os.path.join(french_dir, os.path.relpath(english_file, english_dir))

                if not os.path.exists(french_file):
                    print(f"Fichier correspondant introuvable pour : {english_file}")
                    continue

                # Calculer le chemin relatif par rapport au répertoire anglais
                relative_path = os.path.relpath(english_file, english_dir)
                # Construire le chemin du fichier de sortie
                output_file_dir = os.path.join(output_dir, os.path.dirname(relative_path))
                output_file = os.path.join(output_file_dir, f"{os.path.splitext(file)[0]}.csv")

                # Créer les répertoires nécessaires dans le répertoire de sortie
                if not os.path.exists(output_file_dir):
                    os.makedirs(output_file_dir)

                print(f"Traitement de : {english_file} et {french_file}")

                try:
                    english_data = load_yaml(english_file)
                    french_data = load_yaml(french_file)

                    english_phrases = extract_phrases(english_data)
                    french_phrases = extract_phrases(french_data)

                    save_phrases_to_csv(english_phrases, french_phrases, output_file)
                except Exception as e:
                    print(f"Erreur lors du traitement du fichier {english_file} : {e}")

def main():
    try:
        print("Début du script")
        print("Veuillez sélectionner les répertoires.")
        english_dir = select_directory("Sélectionnez le répertoire contenant les fichiers YAML en anglais")
        french_dir = select_directory("Sélectionnez le répertoire contenant les fichiers YAML en français")
        output_dir = select_directory("Sélectionnez le répertoire pour sauvegarder les fichiers CSV")

        if not english_dir or not french_dir or not output_dir:
            print("Tous les répertoires doivent être sélectionnés pour continuer.")
            return

        process_directories(english_dir, french_dir, output_dir)
        print("Traitement terminé.")
        input("Appuyez sur Entrée pour fermer...")
    except Exception as e:
        print(f"Erreur générale : {e}")
        input("Appuyez sur Entrée pour fermer...")

if __name__ == "__main__":
    main()
