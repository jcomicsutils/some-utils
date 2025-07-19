import os
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

# Try to import py7zr for handling 7z files.
try:
    import py7zr
    py7zr_available = True
except ImportError:
    py7zr_available = False

def process_archive(file_path):
    """Extract internal names and determine the unique top-level folder."""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".zip":
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                names = zf.namelist()
        except Exception as e:
            return None, f"Error reading ZIP file: {e}"
    elif ext == ".7z":
        if not py7zr_available:
            return None, "py7zr module is not installed; cannot process 7z files."
        try:
            with py7zr.SevenZipFile(file_path, 'r') as archive:
                names = archive.getnames()
        except Exception as e:
            return None, f"Error reading 7z file: {e}"
    else:
        return None, "Unsupported file type."

    top_levels = set()
    for name in names:
        parts = [p for p in name.split('/') if p]
        if parts:
            top_levels.add(parts[0])
    
    if len(top_levels) != 1:
        if not top_levels:
            return None, "Archive does not contain any folder."
        else:
            return None, "Archive does not contain exactly one top-level folder."
    
    return top_levels.pop(), None

def rename_archive(file_path, folder_name):
    """Rename the archive to match its internal folder name."""
    dir_name = os.path.dirname(file_path)
    ext = os.path.splitext(file_path)[1]
    new_path = os.path.join(dir_name, folder_name + ext)
    if os.path.exists(new_path):
        return f"Target file '{new_path}' already exists."
    try:
        os.rename(file_path, new_path)
    except Exception as e:
        return f"Error renaming file: {e}"
    return None

def process_single_file(file_path, log_func):
    """Process a single archive file and log results."""
    filename = os.path.basename(file_path)
    log_func(f"Processing: {filename}")
    folder_name, error = process_archive(file_path)
    if error:
        log_func(f"  Error: {error}")
    else:
        err = rename_archive(file_path, folder_name)
        if err:
            log_func(f"  Error: {err}")
        else:
            new_name = f"{folder_name}{os.path.splitext(file_path)[1]}"
            log_func(f"  Renamed to: {new_name}")

def process_folder(folder, log_func, recursive=False):
    """Process archives in the folder (and subfolders if recursive)."""
    if recursive:
        for dirpath, _, filenames in os.walk(folder):
            for filename in filenames:
                if filename.lower().endswith((".zip", ".7z")):
                    file_path = os.path.join(dirpath, filename)
                    process_single_file(file_path, log_func)
    else:
        for entry in os.listdir(folder):
            file_path = os.path.join(folder, entry)
            if os.path.isfile(file_path) and file_path.lower().endswith((".zip", ".7z")):
                process_single_file(file_path, log_func)
    log_func("Processing complete.\n")

class ArchiveRenamerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Archive Renamer")
        self.include_subfolders = tk.BooleanVar(value=False)
        self.create_widgets()

    def create_widgets(self):
        # Top frame for folder selection
        top_frame = tk.Frame(self.root)
        top_frame.pack(padx=10, pady=10, fill=tk.X)

        self.folder_label = tk.Label(top_frame, text="No folder selected")
        self.folder_label.pack(side=tk.LEFT, expand=True, fill=tk.X)

        select_btn = tk.Button(top_frame, text="Select Folder", command=self.select_folder)
        select_btn.pack(side=tk.LEFT, padx=5)

        process_btn = tk.Button(top_frame, text="Process Files", command=self.process_files)
        process_btn.pack(side=tk.LEFT, padx=5)

        # Checkbox for subfolders
        options_frame = tk.Frame(self.root)
        options_frame.pack(padx=10, pady=5, anchor=tk.W)
        tk.Checkbutton(
            options_frame, 
            text="Include Subfolders", 
            variable=self.include_subfolders
        ).pack(side=tk.LEFT)

        # Log area
        self.log_area = scrolledtext.ScrolledText(self.root, height=15, width=70, state=tk.DISABLED)
        self.log_area.pack(padx=10, pady=(0,10), fill=tk.BOTH, expand=True)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path = folder
            self.folder_label.config(text=folder)
            self.log(f"Selected folder: {folder}\n")

    def process_files(self):
        if not hasattr(self, "folder_path"):
            messagebox.showwarning("Warning", "Please select a folder first.")
            return
        self.log("Starting processing...")
        process_folder(self.folder_path, self.log, self.include_subfolders.get())

    def log(self, message):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

def main():
    root = tk.Tk()
    ArchiveRenamerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()