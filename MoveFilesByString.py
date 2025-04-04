import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

def select_source_folder():
    folder = filedialog.askdirectory(title="Select Source Folder")
    if folder:
        source_folder_var.set(folder)

def select_destination_folder():
    folder = filedialog.askdirectory(title="Select Destination Folder")
    if folder:
        destination_folder_var.set(folder)

def move_files():
    source_folder = source_folder_var.get()
    destination_folder = destination_folder_var.get()
    search_string = search_string_var.get()

    if not source_folder or not destination_folder or not search_string:
        messagebox.showerror("Error", "Please fill all fields!")
        return

    if not os.path.exists(source_folder):
        messagebox.showerror("Error", "Source folder does not exist!")
        return

    if not os.path.exists(destination_folder):
        messagebox.showerror("Error", "Destination folder does not exist!")
        return

    moved_files = []
    for file_name in os.listdir(source_folder):
        if search_string in file_name:
            source_path = os.path.join(source_folder, file_name)
            destination_path = os.path.join(destination_folder, file_name)

            if os.path.isfile(source_path):
                shutil.move(source_path, destination_path)
                moved_files.append(file_name)

    if moved_files:
        messagebox.showinfo("Success", f"Moved {len(moved_files)} file(s):\n" + "\n".join(moved_files))
    else:
        messagebox.showinfo("Info", "No files matched the search string.")

# Create the main application window
root = tk.Tk()
root.title("File Mover")
root.geometry("500x300")

# Variables
source_folder_var = tk.StringVar()
destination_folder_var = tk.StringVar()
search_string_var = tk.StringVar()

# Widgets
source_label = tk.Label(root, text="Source Folder:")
source_label.pack(pady=5)
source_entry = tk.Entry(root, textvariable=source_folder_var, width=50)
source_entry.pack(pady=5)
source_button = tk.Button(root, text="Browse", command=select_source_folder)
source_button.pack(pady=5)

destination_label = tk.Label(root, text="Destination Folder:")
destination_label.pack(pady=5)
destination_entry = tk.Entry(root, textvariable=destination_folder_var, width=50)
destination_entry.pack(pady=5)
destination_button = tk.Button(root, text="Browse", command=select_destination_folder)
destination_button.pack(pady=5)

search_string_label = tk.Label(root, text="Search String:")
search_string_label.pack(pady=5)
search_string_entry = tk.Entry(root, textvariable=search_string_var, width=50)
search_string_entry.pack(pady=5)

move_button = tk.Button(root, text="Move Files", command=move_files)
move_button.pack(pady=20)

# Run the application
root.mainloop()