import os
import shutil
import tkinter as tk
from tkinter import filedialog, scrolledtext
import sys
from collections import defaultdict

# Custom class to redirect stdout to a tkinter Text widget
class TextWidgetRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.original_stdout = sys.stdout # Keep a reference to the original stdout

    def write(self, s):
        self.text_widget.insert(tk.END, s)
        self.text_widget.see(tk.END) # Auto-scroll to the end
        self.text_widget.update_idletasks() # Update GUI immediately for responsiveness

    def flush(self):
        self.original_stdout.flush() # Keep original flush behavior


def move_items_simple(source_folder: str, item_names_list_str: str, destination_folder: str, is_folder_mode: bool):
    """
    Moves specified files or folders from a source folder to a destination folder.
    Prints output to the redirected sys.stdout (which goes to the log_widget).

    Args:
        source_folder (str): The path to the source directory.
        item_names_list_str (str): A string containing file/folder names, separated by newlines.
                                   If is_folder_mode is False, each name must include its extension.
        destination_folder (str): The path to the destination directory.
        is_folder_mode (bool): True if moving folders, False if moving files.
    """
    item_type = "folder" if is_folder_mode else "file"
    check_func = os.path.isdir if is_folder_mode else os.path.isfile

    item_names = [f.strip() for f in item_names_list_str.split('\n') if f.strip()]

    print(f"Attempting to move {item_type}s from '{source_folder}' to '{destination_folder}'")
    print(f"{item_type.capitalize()}s to move: {item_names}\n")

    if not os.path.isdir(source_folder):
        print(f"Error: Source folder '{source_folder}' does not exist.")
        return

    os.makedirs(destination_folder, exist_ok=True)
    print(f"Destination folder '{destination_folder}' ensures existence.\n")

    moved_count = 0
    failed_moves = []

    for item_name in item_names:
        source_item_path = os.path.join(source_folder, item_name)
        destination_item_path = os.path.join(destination_folder, item_name)

        if not check_func(source_item_path):
            print(f"Warning: {item_type.capitalize()} '{item_name}' not found in '{source_folder}'. Skipping.")
            failed_moves.append(item_name)
            continue

        try:
            shutil.move(source_item_path, destination_item_path)
            print(f"Successfully moved '{item_name}' ({item_type}) to '{destination_folder}'.")
            moved_count += 1
        except Exception as e:
            print(f"Error moving '{item_name}' ({item_type}): {e}")
            failed_moves.append(item_name)

    print(f"\n--- Summary ---")
    print(f"Total {item_type}s requested: {len(item_names)}")
    print(f"Items successfully moved: {moved_count}")
    if failed_moves:
        print(f"Items that could not be moved: {len(failed_moves)}")
        print("  - " + "\n  - ".join(failed_moves))
    else:
        print(f"All specified {item_type}s were moved successfully.")

    print(f"\nOperation Complete: {item_type.capitalize()} movement complete. {moved_count} {item_type}s moved.")


def selective_move_logic(source_folder: str, item_names_list_str: str, destination_folder: str):
    """
    Performs a selective move operation based on parsed folder/file groups.
    If all listed files for a folder are present and no extra files exist, moves the whole folder.
    Otherwise, moves only the listed files from that folder.
    Prints output to the redirected sys.stdout (which goes to the log_widget).
    """
    lines = [line.strip() for line in item_names_list_str.split('\n') if line.strip()]
    parsed_groups = []
    current_folder_name = None
    current_files_in_list = []

    # Parse the input string into (folder_name, [files]) groups
    for line in lines:
        if '.' not in line or '/' in line or '\\' in line:
            if current_folder_name is not None:
                parsed_groups.append((current_folder_name, current_files_in_list))
            current_folder_name = line.strip('/\\')
            current_files_in_list = []
        else:
            if current_folder_name is None:
                print(f"Warning: File '{line}' found before any folder definition. Skipping.")
                continue
            current_files_in_list.append(line)

    if current_folder_name is not None:
        parsed_groups.append((current_folder_name, current_files_in_list))

    print(f"Parsed groups for selective move: {parsed_groups}\n")

    if not os.path.isdir(source_folder):
        print(f"Error: Source folder '{source_folder}' does not exist.")
        return

    os.makedirs(destination_folder, exist_ok=True)
    print(f"Destination root folder '{destination_folder}' ensures existence.\n")

    for folder_name, files_in_list in parsed_groups:
        full_source_folder_path = os.path.join(source_folder, folder_name)
        full_dest_folder_path = os.path.join(destination_folder, folder_name)

        if not os.path.isdir(full_source_folder_path):
            print(f"Warning: Source folder '{folder_name}' not found in '{source_folder}'. Skipping its associated files.")
            continue

        actual_files_in_source_folder = {f for f in os.listdir(full_source_folder_path) if os.path.isfile(os.path.join(full_source_folder_path, f))}
        required_files_set = set(files_in_list)

        all_required_present = required_files_set.issubset(actual_files_in_source_folder)
        extra_files_present = bool(actual_files_in_source_folder - required_files_set)

        print(f"\nProcessing folder '{folder_name}':")
        if all_required_present and not extra_files_present:
            print(f"  Condition met: All required files present and no extra files. Moving entire folder.")
            try:
                shutil.move(full_source_folder_path, full_dest_folder_path)
                print(f"  Successfully moved folder '{folder_name}' to '{destination_folder}'.")
            except Exception as e:
                print(f"  Error moving entire folder '{folder_name}': {e}")
        else:
            print(f"  Condition not met: Moving specific files only.")
            if not all_required_present:
                missing_required = required_files_set - actual_files_in_source_folder
                print(f"  Warning: Missing required files in '{folder_name}': {', '.join(missing_required)}")
            if extra_files_present:
                extra_files = actual_files_in_source_folder - required_files_set
                print(f"  Note: Extra files found in '{folder_name}' that will remain: {', '.join(extra_files)}")

            os.makedirs(full_dest_folder_path, exist_ok=True)
            for file_name in files_in_list:
                source_file_path = os.path.join(full_source_folder_path, file_name)
                dest_file_path = os.path.join(full_dest_folder_path, file_name)
                if os.path.isfile(source_file_path):
                    try:
                        shutil.move(source_file_path, dest_file_path)
                        print(f"  Moved file '{file_name}' from '{folder_name}' to '{full_dest_folder_path}'.")
                    except Exception as e:
                        print(f"  Error moving file '{file_name}' from '{folder_name}': {e}")
                else:
                    print(f"  Warning: File '{file_name}' not found in '{folder_name}'. Skipping.")

    print("\nOperation Complete: Selective move operation finished.")

def archive_style_move_logic(source_folder: str, item_names_list_str: str, destination_folder: str):
    """
    Performs a move operation based on a list format like 'folder/file.ext'.
    It groups files by folder. If all files in a local source sub-folder are present in the
    provided list, the entire folder is moved. If the destination folder already exists,
    the contents are merged. Otherwise, only the specified files are moved.
    """
    lines = [line.strip() for line in item_names_list_str.split('\n') if line.strip()]
    
    folders_moved = 0
    files_moved = 0
    failed_items = []

    # Use defaultdict to easily group files by their parent directory
    parsed_groups = defaultdict(list)
    
    print("--- Parsing Archive-Style List ---")
    for line in lines:
        # Normalize path separators for consistency before splitting
        path = line.replace('\\', '/')
        dir_name, file_name = os.path.split(path)

        if not file_name: # Skip if line is just a directory name
            print(f"Skipping directory-only entry: '{line}'")
            continue

        if dir_name:
            parsed_groups[dir_name].append(file_name)
        else:
            # Use a special key for files in the root of the source folder
            parsed_groups['__ROOT__'].append(file_name)
    
    print(f"Parsed {len(parsed_groups) + ('__ROOT__' in parsed_groups)} groups for moving.\n")

    if not os.path.isdir(source_folder):
        print(f"Error: Source folder '{source_folder}' does not exist.")
        return

    os.makedirs(destination_folder, exist_ok=True)
    print(f"Destination root folder '{destination_folder}' ensured to exist.\n")

    # --- Process root files first ---
    if '__ROOT__' in parsed_groups:
        root_files_to_move = parsed_groups.pop('__ROOT__')
        print("--- Processing Root Files ---")
        for file_name in root_files_to_move:
            source_file_path = os.path.join(source_folder, file_name)
            dest_file_path = os.path.join(destination_folder, file_name)
            if os.path.isfile(source_file_path):
                try:
                    shutil.move(source_file_path, dest_file_path)
                    print(f"Moved root file '{file_name}' to '{destination_folder}'.")
                    files_moved += 1
                except Exception as e:
                    print(f"Error moving root file '{file_name}': {e}")
                    failed_items.append(file_name)
            else:
                print(f"Warning: Root file '{file_name}' not found in '{source_folder}'. Skipping.")
        print("--- Finished Processing Root Files ---\n")

    # --- Process sub-folders ---
    print("--- Processing Sub-folders ---")
    for folder_name, files_in_list in parsed_groups.items():
        full_source_folder_path = os.path.join(source_folder, folder_name)
        full_dest_folder_path = os.path.join(destination_folder, folder_name)

        print(f"\nProcessing folder '{folder_name}':")
        if not os.path.isdir(full_source_folder_path):
            print(f"  Warning: Source folder '{folder_name}' not found in '{source_folder}'. Skipping this group.")
            failed_items.append(folder_name + " (source not found)")
            continue

        actual_files_in_source_folder = {f for f in os.listdir(full_source_folder_path) if os.path.isfile(os.path.join(full_source_folder_path, f))}
        required_files_set = set(files_in_list)
        
        if actual_files_in_source_folder.issubset(required_files_set):
            print(f"  Condition met: All local files are in the archive list. Moving entire folder.")
            
            try:
                if os.path.isdir(full_dest_folder_path):
                    print(f"  Destination '{folder_name}' already exists. Merging contents.")
                    # Move each item from source to destination, overwriting if necessary
                    for item in os.listdir(full_source_folder_path):
                        s_item = os.path.join(full_source_folder_path, item)
                        d_item = os.path.join(full_dest_folder_path, item)
                        shutil.move(s_item, d_item)
                    os.rmdir(full_source_folder_path) # Remove the now-empty source folder
                    print(f"  Successfully merged folder '{folder_name}' into '{destination_folder}'.")
                else:
                    # Destination does not exist, move the folder directly
                    shutil.move(full_source_folder_path, destination_folder) 
                    print(f"  Successfully moved folder '{folder_name}' to '{destination_folder}'.")
                folders_moved += 1
            except Exception as e:
                print(f"  Error processing folder '{folder_name}': {e}")
                failed_items.append(folder_name)
        else:
            # Scenario B: Local folder has files not in the list. Move only the specified files.
            print(f"  Condition not met: Moving specific files only.")
            missing_from_list = actual_files_in_source_folder - required_files_set
            print(f"  Note: Local files not in archive list (will be left behind): {', '.join(missing_from_list)}")

            os.makedirs(full_dest_folder_path, exist_ok=True)
            for file_name in files_in_list:
                source_file_path = os.path.join(full_source_folder_path, file_name)
                dest_file_path = os.path.join(full_dest_folder_path, file_name)
                if os.path.isfile(source_file_path):
                    try:
                        shutil.move(source_file_path, dest_file_path)
                        print(f"  Moved file '{file_name}' to '{full_dest_folder_path}'.")
                        files_moved += 1
                    except Exception as e:
                        print(f"  Error moving file '{file_name}': {e}")
                        failed_items.append(os.path.join(folder_name, file_name))
                else:
                    pass

    print(f"\n--- Summary ---")
    print(f"Total lines in list: {len(lines)}")
    print(f"Folders processed/moved completely: {folders_moved}")
    print(f"Individual files moved: {files_moved}")
    if failed_items:
        print(f"Items that had issues: {len(failed_items)}")
        print("  - " + "\n  - ".join(failed_items))
    else:
        print("All specified items were processed successfully.")
    
    print("\nOperation Complete: Archive-style move operation finished.")

class FileMoverApp:
    def __init__(self, master):
        self.master = master
        master.title("File/Folder Mover GUI")
        master.geometry("800x650") 
        master.resizable(True, True)

        # Boolean variables for mutual exclusive checkboxes
        self.is_file_mode = tk.BooleanVar(value=True)
        self.is_folder_mode = tk.BooleanVar(value=False)
        self.is_selective_mode = tk.BooleanVar(value=False)
        self.is_archive_style_mode = tk.BooleanVar(value=False) # New mode variable

        self.create_widgets()
        self.update_filenames_label()

    def create_widgets(self):
        # Frame for Source Folder
        source_frame = tk.LabelFrame(self.master, text="Source Folder", padx=10, pady=10)
        source_frame.pack(padx=10, pady=5, fill="x", expand=False)

        self.source_path_entry = tk.Entry(source_frame, width=60)
        self.source_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        source_browse_button = tk.Button(source_frame, text="Browse", command=self.browse_source_folder)
        source_browse_button.pack(side="right")

        # Mode Selection Frame for checkboxes
        mode_selection_frame = tk.LabelFrame(self.master, text="Operation Mode", padx=10, pady=5)
        mode_selection_frame.pack(padx=10, pady=5, fill="x")

        self.file_checkbox = tk.Checkbutton(mode_selection_frame, text="Move Files (direct)", variable=self.is_file_mode, command=lambda: self.set_mode(self.is_file_mode))
        self.file_checkbox.pack(side="left", padx=5)

        self.folder_checkbox = tk.Checkbutton(mode_selection_frame, text="Move Folders (direct)", variable=self.is_folder_mode, command=lambda: self.set_mode(self.is_folder_mode))
        self.folder_checkbox.pack(side="left", padx=5)

        self.selective_checkbox = tk.Checkbutton(mode_selection_frame, text="Selective Folder/File Move", variable=self.is_selective_mode, command=lambda: self.set_mode(self.is_selective_mode))
        self.selective_checkbox.pack(side="left", padx=5)
        
        # New checkbox for the archive-style move
        self.archive_style_checkbox = tk.Checkbutton(mode_selection_frame, text="Archive Style Move", variable=self.is_archive_style_mode, command=lambda: self.set_mode(self.is_archive_style_mode))
        self.archive_style_checkbox.pack(side="left", padx=5)


        # Frame for Items List (Filenames/Foldernames)
        self.files_frame_label = tk.LabelFrame(self.master, text="Items to Move", padx=10, pady=10)
        self.files_frame_label.pack(padx=10, pady=5, fill="both", expand=True)

        self.filenames_text_area = scrolledtext.ScrolledText(self.files_frame_label, wrap=tk.WORD, height=10)
        self.filenames_text_area.pack(fill="both", expand=True)

        # Frame for Destination Folder
        dest_frame = tk.LabelFrame(self.master, text="Destination Folder", padx=10, pady=10)
        dest_frame.pack(padx=10, pady=5, fill="x", expand=False)

        self.dest_path_entry = tk.Entry(dest_frame, width=60)
        self.dest_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        dest_browse_button = tk.Button(dest_frame, text="Browse", command=self.browse_destination_folder)
        dest_browse_button.pack(side="right")

        # Move Button
        move_button = tk.Button(self.master, text="Perform Move Operation", command=self.execute_move)
        move_button.pack(pady=10)

        # Log Output Area
        log_frame = tk.LabelFrame(self.master, text="Log Output", padx=10, pady=10)
        log_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.log_text_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=8, state='normal')
        self.log_text_area.pack(fill="both", expand=True)
        self.log_text_area.config(state='disabled')

    def set_mode(self, mode_var_to_set):
        """Ensures mutual exclusivity of the mode checkboxes."""
        all_modes = [self.is_file_mode, self.is_folder_mode, self.is_selective_mode, self.is_archive_style_mode]
        
        for mode in all_modes:
            if mode != mode_var_to_set:
                mode.set(False)

        # Ensure the clicked mode is set to True
        mode_var_to_set.set(True)
        self.update_filenames_label()

    def update_filenames_label(self):
        """Updates the label of the items list based on the active mode."""
        if self.is_file_mode.get():
            self.files_frame_label.config(text="Files to Move (one per line, with extension)")
        elif self.is_folder_mode.get():
            self.files_frame_label.config(text="Folders to Move (one per line)")
        elif self.is_selective_mode.get():
            self.files_frame_label.config(text="Selective Move: Folder then Files (e.g., folder1\\nfile1.txt\\n...)")
        elif self.is_archive_style_mode.get():
            self.files_frame_label.config(text="Archive Style: Paste List (e.g., folderA/file1.txt)")
        else:
            self.files_frame_label.config(text="Items to Move (select an operation mode above)")


    def browse_source_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.source_path_entry.delete(0, tk.END)
            self.source_path_entry.insert(0, folder_selected)

    def browse_destination_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.dest_path_entry.delete(0, tk.END)
            self.dest_path_entry.insert(0, folder_selected)

    def execute_move(self):
        source_folder = self.source_path_entry.get()
        item_names_list_str = self.filenames_text_area.get("1.0", tk.END)
        destination_folder = self.dest_path_entry.get()

        self.log_text_area.config(state='normal')
        self.log_text_area.delete("1.0", tk.END)

        if not source_folder or not destination_folder:
            print("Warning: Please select both source and destination folders.\n")
            self.log_text_area.config(state='disabled')
            return

        original_stdout = sys.stdout
        sys.stdout = TextWidgetRedirector(self.log_text_area)

        try:
            if self.is_file_mode.get():
                move_items_simple(source_folder, item_names_list_str, destination_folder, False)
            elif self.is_folder_mode.get():
                move_items_simple(source_folder, item_names_list_str, destination_folder, True)
            elif self.is_selective_mode.get():
                selective_move_logic(source_folder, item_names_list_str, destination_folder)
            elif self.is_archive_style_mode.get():
                archive_style_move_logic(source_folder, item_names_list_str, destination_folder)
            else:
                print("Warning: Please select an operation mode.\n")

        finally:
            sys.stdout = original_stdout
            self.log_text_area.config(state='disabled')


if __name__ == "__main__":
    root = tk.Tk()
    app = FileMoverApp(root)
    root.mainloop()