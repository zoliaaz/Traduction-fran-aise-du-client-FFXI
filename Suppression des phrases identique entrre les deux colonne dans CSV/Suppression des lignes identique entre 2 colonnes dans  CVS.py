import os
import csv
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

def process_csv_file(file_path):
    """Traite un fichier CSV pour supprimer les phrases en français qui sont identiques à celles en anglais."""
    try:
        # Lire le contenu du fichier CSV en mode binaire pour ignorer les caractères NUL
        with open(file_path, mode='rb') as file:
            content = file.read().replace(b'\x00', b'')  # Supprimer les caractères NUL

        # Reconvertir en chaîne de caractères pour lecture CSV
        content = content.decode('utf-8', errors='ignore').splitlines()

        # Lire le contenu du fichier CSV
        reader = csv.reader(content, delimiter=';')
        rows = list(reader)

        # Extraire les phrases en anglais et en français
        english_phrases = [row[0] for row in rows]
        french_phrases = [row[1] for row in rows]

        # Déterminer les phrases à supprimer
        phrases_to_remove = set(english_phrases) & set(french_phrases)

        # Créer un nouveau contenu sans les phrases à supprimer de la colonne 2 (français)
        new_rows = [[row[0], row[1] if row[1] not in phrases_to_remove else ''] for row in rows]

        # Écrire le contenu modifié dans le fichier CSV
        with open(file_path, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerows(new_rows)

    except Exception as e:
        # Afficher un message d'erreur en cas de problème
        messagebox.showerror("Erreur", f"Une erreur est survenue lors du traitement du fichier {file_path}:\n{e}")

def process_folder(folder_path):
    """Parcourt tous les fichiers CSV dans un dossier et les traite."""
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(folder_path, filename)
            process_csv_file(file_path)
            print(f"Processed {filename}")

def select_folder():
    """Ouvre une boîte de dialogue pour permettre à l'utilisateur de sélectionner un dossier."""
    root = tk.Tk()
    root.withdraw()  # Cacher la fenêtre principale
    folder_path = filedialog.askdirectory()  # Ouvrir le sélecteur de dossier
    if folder_path:
        process_folder(folder_path)
        messagebox.showinfo("Processus terminé", "Le traitement des fichiers CSV est terminé.")
        root.mainloop()  # Garde la fenêtre ouverte jusqu'à ce que l'utilisateur la ferme

# Point d'entrée du script
if __name__ == "__main__":
    select_folder()
