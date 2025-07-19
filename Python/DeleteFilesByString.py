import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar, Style, Button, Label, Entry, Checkbutton

# Event to control stopping the thread
stop_event = threading.Event()

def delete_files_with_string(directory, target_string, exact_match, progress_callback):
    """
    Deletes files in the given directory based on the mode:
    - Exact match: Deletes files with an exact name match.
    - Contains string: Deletes files containing the string in their filenames.
    Updates progress via a callback.
    """
    try:
        if exact_match:
            files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and f == target_string]
        else:
            files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and target_string in f]

        total_files = len(files)
        
        for index, filename in enumerate(files):
            if stop_event.is_set():
                print("Deletion stopped by user.")
                break
            
            file_path = os.path.join(directory, filename)
            os.remove(file_path)
            print(f"Deleted: {file_path}")
            
            # Update progress
            progress_callback(index + 1, total_files)
        
        if not stop_event.is_set():
            progress_callback(total_files, total_files)
            # messagebox.showinfo("Completed", "File deletion completed successfully.")
        else:
            messagebox.showinfo("Stopped", "File deletion was stopped.")
    
    except Exception as e:
        print(f"An error occurred: {e}")
        messagebox.showerror("Error", f"An error occurred: {e}")

def start_deletion(directory, target_string, exact_match, progress_callback):
    """Starts the deletion process in a separate thread."""
    stop_event.clear()
    thread = threading.Thread(target=delete_files_with_string, args=(directory, target_string, exact_match, progress_callback))
    thread.start()

def browse_directory(entry_widget):
    """Opens a dialog to browse and select a directory."""
    directory = filedialog.askdirectory()
    if directory:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, directory)

def paste_clipboard(entry_widget):
    """Pastes the clipboard content into the given entry widget."""
    clipboard_content = root.clipboard_get()
    entry_widget.delete(0, tk.END)
    entry_widget.insert(0, clipboard_content)

def create_gui():
    global root
    root = tk.Tk()
    root.title("File Deletion Tool with Progress")
    root.geometry("600x300")  # Set consistent window size

    # Set a style
    style = Style()
    style.configure("TLabel", font=("Helvetica", 12))
    style.configure("TButton", font=("Helvetica", 10))
    style.configure("TEntry", font=("Helvetica", 10))

    # Directory selection
    Label(root, text="Directory:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
    directory_entry = Entry(root, width=50)
    directory_entry.grid(row=0, column=1, padx=10, pady=10)
    Button(root, text="Browse", command=lambda: browse_directory(directory_entry)).grid(row=0, column=2, padx=10, pady=10)
    
    # Target string
    Label(root, text="Target String:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
    target_string_entry = Entry(root, width=50)
    target_string_entry.grid(row=1, column=1, padx=10, pady=10)
    Button(root, text="Paste", command=lambda: paste_clipboard(target_string_entry)).grid(row=1, column=2, padx=10, pady=10)
    
    # Progress bar
    progress_var = tk.IntVar()
    progress_bar = Progressbar(root, variable=progress_var, maximum=100)
    progress_bar.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="ew")

    def update_progress(current, total):
        """Updates the progress bar."""
        if total > 0:
            progress = int((current / total) * 100)
            progress_var.set(progress)
            root.update_idletasks()

    # Mode selection (exact match vs contains string)
    exact_match_var = tk.BooleanVar(value=False)  # Default: Contains string
    Checkbutton(root, text="Exact Filename Match", variable=exact_match_var).grid(row=3, column=0, columnspan=2, pady=10, sticky="w")

    # Delete button
    def on_delete_button_click():
        directory = directory_entry.get()
        target_string = target_string_entry.get()
        exact_match = exact_match_var.get()
        if not directory or not os.path.isdir(directory):
            messagebox.showwarning("Invalid Directory", "Please select a valid directory.")
            return
        if not target_string:
            messagebox.showwarning("Invalid Input", "Please enter a target string.")
            return
        progress_var.set(0)
        start_deletion(directory, target_string, exact_match, update_progress)

    Button(root, text="Delete Files", command=on_delete_button_click).grid(row=4, column=0, columnspan=2, pady=10)

    # Stop button
    def on_stop_button_click():
        stop_event.set()

    Button(root, text="Stop", command=on_stop_button_click).grid(row=4, column=2, pady=10)
    
    root.mainloop()

# Uncomment to run the GUI
create_gui()