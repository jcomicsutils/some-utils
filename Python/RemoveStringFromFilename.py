import os
import tkinter as tk
from tkinter import filedialog, messagebox

class RenamerApp:
    def __init__(self, master):
        self.master = master
        master.title("Filename String Remover")

        # Folder selection
        self.folder_label = tk.Label(master, text="Folder:")
        self.folder_label.grid(row=0, column=0, padx=5, pady=5)

        self.folder_entry = tk.Entry(master, width=50)
        self.folder_entry.grid(row=0, column=1, padx=5, pady=5)

        self.browse_button = tk.Button(master, text="Browse", command=self.browse_folder)
        self.browse_button.grid(row=0, column=2, padx=5, pady=5)

        # Target string
        self.target_label = tk.Label(master, text="String to remove:")
        self.target_label.grid(row=1, column=0, padx=5, pady=5)

        self.target_entry = tk.Entry(master, width=50)
        self.target_entry.grid(row=1, column=1, padx=5, pady=5)

        # Process button
        self.process_button = tk.Button(master, text="Remove String from Filenames", command=self.rename_files)
        self.process_button.grid(row=2, column=1, padx=5, pady=5)

        # Status label
        self.status_label = tk.Label(master, text="")
        self.status_label.grid(row=3, column=0, columnspan=3, padx=5, pady=5)

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder_path)

    def rename_files(self):
        folder_path = self.folder_entry.get()
        target = self.target_entry.get().strip()

        if not folder_path or not target:
            self.status_label.config(text="Please select a folder and enter a string to remove.")
            return

        if not os.path.isdir(folder_path):
            self.status_label.config(text="Invalid folder path.")
            return

        success = 0
        errors = 0

        try:
            for filename in os.listdir(folder_path):
                old_path = os.path.join(folder_path, filename)
                
                if os.path.isfile(old_path):
                    new_filename = filename.replace(target, '')
                    
                    if new_filename != filename:
                        new_path = os.path.join(folder_path, new_filename)
                        
                        try:
                            os.rename(old_path, new_path)
                            success += 1
                        except Exception as e:
                            errors += 1
                            
            self.status_label.config(text=f"Operation complete! Successful renames: {success}, Errors: {errors}")
            
        except Exception as e:
            self.status_label.config(text=f"An error occurred: {str(e)}")
            

if __name__ == "__main__":
    root = tk.Tk()
    app = RenamerApp(root)
    root.mainloop()