import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog
from time import sleep

def select_folder():
    """Fonction pour sélectionner un dossier."""
    root = tk.Tk()
    root.withdraw()  # Masque la fenêtre principale de Tkinter
    folder_selected = filedialog.askdirectory()
    return folder_selected

def find_common_phrases(folder, min_files=10):
    """Trouve les phrases communes dans au moins `min_files` fichiers CSV."""
    phrase_count = {}
    csv_files = [f for f in os.listdir(folder) if f.endswith('.csv')]
    total_files = len(csv_files)

    # Lire tous les fichiers CSV dans le dossier
    for i, filename in enumerate(csv_files):
        file_path = os.path.join(folder, filename)
        df = pd.read_csv(file_path, sep=";", usecols=[0], header=None)
        phrases = df[0].tolist()
        
        # Compter les occurrences de chaque phrase
        unique_phrases = set(phrases)
        for phrase in unique_phrases:
            if phrase in phrase_count:
                phrase_count[phrase] += 1
            else:
                phrase_count[phrase] = 1

        # Afficher le pourcentage de progression
        progress = (i + 1) / total_files * 100
        print(f"Traitement en cours : {progress:.2f}%", end='\r')

    # Filtrer les phrases qui apparaissent dans plus de `min_files` fichiers
    common_phrases = [phrase for phrase, count in phrase_count.items() if count > min_files]

    return common_phrases

def save_common_phrases(common_phrases, output_folder):
    """Sauvegarde les phrases communes dans un fichier CSV dans le dossier sélectionné."""
    output_file = os.path.join(output_folder, "Table_phrase_commune.csv")
    df = pd.DataFrame(common_phrases, columns=["Phrase en Anglais"])
    df["Phrase en Français"] = ""  # Ajouter une colonne vide pour la traduction
    df.to_csv(output_file, sep=";", index=False)

if __name__ == "__main__":
    folder = select_folder()
    if folder:
        print("Début du traitement...")
        common_phrases = find_common_phrases(folder)
        save_common_phrases(common_phrases, folder)
        print(f"CSV créé avec succès : {os.path.join(folder, 'Table_phrase_commune.csv')}")
        input("Appuyez sur Entrée pour fermer le programme.")
    else:
        print("Aucun dossier n'a été sélectionné.")
