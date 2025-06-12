import os
import tkinter as tk
from tkinter import filedialog

def get_filenames_without_extension(folder_path):
    filenames = []
    for entry in os.listdir(folder_path):
        full_path = os.path.join(folder_path, entry)
        if os.path.isfile(full_path):
            name, _ = os.path.splitext(entry)
            filenames.append(name)
    return filenames

def select_folder_and_get_filenames():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    folder_selected = filedialog.askdirectory(title="Select a Folder")
    
    if folder_selected:
        filenames = get_filenames_without_extension(folder_selected)
        print("Filenames without extensions:")
        for name in filenames:
            print(name)
    else:
        print("No folder selected.")

# Run the function
select_folder_and_get_filenames()

