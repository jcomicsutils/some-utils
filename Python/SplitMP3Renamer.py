import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class FileRenamerApp:
    def __init__(self, master):
        self.master = master
        master.title("MP3 File Renamer")
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Create GUI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Folder selection frame
        frame = ttk.Frame(self.master, padding=10)
        frame.grid(row=0, column=0, sticky="ew")
        
        self.folder_entry = ttk.Entry(frame, width=50)
        self.folder_entry.grid(row=0, column=0, padx=5, sticky="ew")
        
        browse_btn = ttk.Button(frame, text="Browse", command=self.browse_folder)
        browse_btn.grid(row=0, column=1, padx=5)
        
        # Process button
        process_btn = ttk.Button(self.master, text="Process Files", command=self.process_files)
        process_btn.grid(row=1, column=0, pady=10)
        
        # Log text area
        self.log_text = tk.Text(self.master, height=15, width=70, wrap=tk.WORD)
        self.log_text.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        
        # Scrollbar for log
        scrollbar = ttk.Scrollbar(self.master, command=self.log_text.yview)
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Configure grid weights
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(2, weight=1)
        
    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder_path)
            
    def log_message(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.master.update_idletasks()
        
    def process_files(self):
        folder_path = self.folder_entry.get()
        if not folder_path:
            messagebox.showerror("Error", "Please select a folder first.")
            return
            
        pattern = re.compile(r'^(.*?)\.mp3(?:\.(\d{3}))(?:\.(\d{3}))?$', re.IGNORECASE)
        processed_files = 0
        
        try:
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                
                if os.path.isfile(file_path):
                    match = pattern.fullmatch(filename)
                    if match:
                        base_name = match.group(1)
                        numbers = list(filter(None, match.groups()[1:]))
                        
                        new_name = f"{base_name}.{'.'.join(numbers)}.mp3"
                        new_path = os.path.join(folder_path, new_name)
                        
                        try:
                            os.rename(file_path, new_path)
                            self.log_message(f"Renamed: {filename} → {new_name}")
                            processed_files += 1
                        except Exception as e:
                            self.log_message(f"Error renaming {filename}: {str(e)}")
                            
            self.log_message(f"\nProcessing complete! {processed_files} files were renamed.")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileRenamerApp(root)
    root.mainloop()