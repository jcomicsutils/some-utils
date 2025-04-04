import os
import tkinter as tk
from tkinter import filedialog, messagebox

def create_file():
    folder_path = folder_entry.get()
    file_name = file_name_entry.get()

    if not folder_path or not file_name:
        messagebox.showerror("Error", "Both folder path and file name are required!")
        return

    if not os.path.isdir(folder_path):
        messagebox.showerror("Error", "The selected folder does not exist!")
        return

    file_path = os.path.join(folder_path, file_name)

    try:
        with open(file_path, 'w') as file:
            file.write("")  # Create an empty file
        #messagebox.showinfo("Success", f"File '{file_name}' created in folder '{folder_path}'.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to create file: {str(e)}")

# Create the main application window
root = tk.Tk()
root.title("File Creator")

# Folder selection
folder_label = tk.Label(root, text="Folder Path:")
folder_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

folder_entry = tk.Entry(root, width=50)
folder_entry.grid(row=0, column=1, padx=10, pady=5)

def browse_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        folder_entry.delete(0, tk.END)
        folder_entry.insert(0, folder_selected)

browse_button = tk.Button(root, text="Browse", command=browse_folder)
browse_button.grid(row=0, column=2, padx=10, pady=5)

# File name input
file_name_label = tk.Label(root, text="File Name:")
file_name_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")

file_name_entry = tk.Entry(root, width=50)
file_name_entry.grid(row=1, column=1, padx=10, pady=5)

# Create file button
create_button = tk.Button(root, text="Create File", command=create_file)
create_button.grid(row=2, column=1, pady=10)

# Run the Tkinter event loop
root.mainloop()