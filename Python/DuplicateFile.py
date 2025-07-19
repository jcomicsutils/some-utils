import os

import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

def duplicate_file(file_path, n, suffix):
    # Check if the file exists
    if not os.path.isfile(file_path):
        print(f"The file {file_path} does not exist.")
        return
    
    # Extract the directory, base name, and extension of the file
    directory, filename = os.path.split(file_path)
    base_name, extension = os.path.splitext(filename)
    
    # Duplicate the file N times
    for i in range(1, n + 1):
        new_filename = f"{base_name}{suffix}{i}{extension}"
        new_file_path = os.path.join(directory, new_filename)
        
        # Copy the file
        shutil.copyfile(file_path, new_file_path)
        print(f"Created: {new_file_path}")
    messagebox.showinfo("Success", f"Duplicated the file {n} times.")

def choose_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        file_path_entry.delete(0, tk.END)
        file_path_entry.insert(0, file_path)

def start_duplication():
    file_path = file_path_entry.get()
    try:
        n = int(copies_entry.get())
        suffix = suffix_entry.get()
        duplicate_file(file_path, n, suffix)
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid number of copies.")

# Create the main window
root = tk.Tk()
root.title("File Duplicator")

# Create and place the widgets
tk.Label(root, text="Choose File:").grid(row=0, column=0, padx=10, pady=10)
file_path_entry = tk.Entry(root, width=50)
file_path_entry.grid(row=0, column=1, padx=10, pady=10)
tk.Button(root, text="Browse", command=choose_file).grid(row=0, column=2, padx=10, pady=10)

tk.Label(root, text="Number of Copies:").grid(row=1, column=0, padx=10, pady=10)
copies_entry = tk.Entry(root, width=10)
copies_entry.grid(row=1, column=1, padx=10, pady=10)

tk.Label(root, text="Suffix for Copies:").grid(row=2, column=0, padx=10, pady=10)
suffix_entry = tk.Entry(root, width=20)
suffix_entry.grid(row=2, column=1, padx=10, pady=10)

tk.Button(root, text="Duplicate", command=start_duplication).grid(row=3, column=1, padx=10, pady=10)

# Start the main event loop
root.mainloop()