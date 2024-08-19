WARNING i'm not a developper, i made this with ChatGPT, or i should say it did it from i question and my suggestion.
This tool is made to work with this https://github.com/zoliaaz/Traduction-fran-aise-du-client-FFXI.

YAML and CSV File Translator
Overview

The YAML and CSV File Translator is a Python application designed to translate phrases in YAML files using a translation table provided in a CSV file. This tool is particularly useful for managing translations in YAML files where phrases might have different IDs or structures, ensuring that translations are accurately applied despite differences in ID conventions.
Features

    Translate Phrases: Automatically translate phrases in YAML files using translations from a CSV file.
    Handle Different IDs: Resolve issues with different IDs or structures between YAML files and their translations by using a direct phrase-to-phrase mapping.
    Preserve YAML Format: Maintain the original formatting of YAML files, including block styles (|-) and quoted strings.
    
    User-Friendly GUI: Simple graphical interface for selecting directories and managing file processing.

How It Works

    File Selection:
        YAML Directory: Select the directory containing YAML files that need translation.
        CSV Directory: Select the directory containing CSV files where the translation table is stored.
        Output Directory: Choose the directory where the translated YAML files will be saved.

    Translation Process:
        The application reads each YAML file and its corresponding CSV file.
        CSV Structure: The CSV file should have two columns:
            The first column contains the original phrases (English).
            The second column contains the translations (French).
        The application updates the YAML files, replacing the original phrases with their translations from the CSV file.
        If a phrase in the YAML file is not found in the CSV file or the French column is empty, it is left unchanged.

    Progress Reporting:
        A progress bar displays the percentage of files processed, providing real-time feedback on the operation's progress.



Usage:

    Follow the Prompts:
        Select the directory containing the YAML files you want to translate.
        Choose the directory containing the CSV files with the translation table.
        Specify the output directory where the translated YAML files will be saved.

    Processing Completion:
        The application processes and translates the YAML files as specified.
        After processing, a completion message will be displayed.

Notes

    Ensure each YAML file has a corresponding CSV file with the same base name but with a .csv extension.
    The CSV file must have at least two columns: the first column for the original phrases and the second column for the translations.
    The software preserves the original YAML formatting, including block styles (|-) and any quoted strings.

Troubleshooting

    File Not Found: Make sure the YAML and CSV files are correctly named and located in the specified directories.
    Dependency Issues: Ensure all required Python packages are installed. Use pip to install any missing packages.

    Contact

For questions or issues, please open an issue on the GitHub repository.
