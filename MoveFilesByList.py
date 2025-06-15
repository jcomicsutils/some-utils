import os
import shutil
import tkinter as tk
from tkinter import filedialog, scrolledtext
import sys

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
    print(f"Files successfully moved: {moved_count}") # Typo fix from "Files" to "Items"
    if failed_moves:
        print(f"Files that could not be moved: {len(failed_moves)}")
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
        # Heuristic: A line without a dot is considered a folder name.
        # A line with a dot is considered a file name.
        if '.' not in line or '/' in line or '\\' in line: # Check for path separators too
            # If the current folder has files, add it to parsed_groups
            if current_folder_name is not None:
                parsed_groups.append((current_folder_name, current_files_in_list))
            current_folder_name = line.strip('/\\') # Remove trailing slashes
            current_files_in_list = []
        else: # Likely a file name
            if current_folder_name is None:
                print(f"Warning: File '{line}' found before any folder definition. Skipping.")
                continue
            current_files_in_list.append(line)

    if current_folder_name is not None: # Add the last group if it exists
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

        # Get actual files (not directories) within the source sub-folder
        actual_files_in_source_folder = set()
        for f in os.listdir(full_source_folder_path):
            if os.path.isfile(os.path.join(full_source_folder_path, f)):
                actual_files_in_source_folder.add(f)

        # Convert files_in_list to a set for efficient lookup
        required_files_set = set(files_in_list)

        # Check if all required files are present in the source sub-folder
        all_required_present = required_files_set.issubset(actual_files_in_source_folder)

        # Check if there are any extra files in the source sub-folder (not in required_files_set)
        extra_files_present = bool(actual_files_in_source_folder - required_files_set)

        print(f"\nProcessing folder '{folder_name}':")
        if all_required_present and not extra_files_present:
            # Scenario A: Move entire folder
            print(f"  Condition met: All required files present and no extra files. Moving entire folder.")
            try:
                shutil.move(full_source_folder_path, full_dest_folder_path)
                print(f"  Successfully moved folder '{folder_name}' to '{destination_folder}'.")
            except Exception as e:
                print(f"  Error moving entire folder '{folder_name}': {e}")
        else:
            # Scenario B: Move only specified files
            print(f"  Condition not met: Moving specific files only.")
            if not all_required_present:
                missing_required = required_files_set - actual_files_in_source_folder
                print(f"  Warning: Missing required files in '{folder_name}': {', '.join(missing_required)}")
            if extra_files_present:
                extra_files = actual_files_in_source_folder - required_files_set
                print(f"  Note: Extra files found in '{folder_name}' that will remain: {', '.join(extra_files)}")

            os.makedirs(full_dest_folder_path, exist_ok=True) # Ensure destination sub-folder exists for specific files
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


class FileMoverApp:
    def __init__(self, master):
        self.master = master
        master.title("File/Folder Mover GUI")
        master.geometry("700x600") # Slightly increased height for new checkbox
        master.resizable(True, True)

        # Boolean variables for mutual exclusive checkboxes
        self.is_file_mode = tk.BooleanVar(value=True) # Default to file mode
        self.is_folder_mode = tk.BooleanVar(value=False)
        self.is_selective_mode = tk.BooleanVar(value=False)

        self.create_widgets()
        # Ensure correct label is set initially based on default mode
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

        self.file_checkbox = tk.Checkbutton(
            mode_selection_frame,
            text="Move Files (direct)",
            variable=self.is_file_mode,
            command=lambda: self.set_mode(self.is_file_mode)
        )
        self.file_checkbox.pack(side="left", padx=5)

        self.folder_checkbox = tk.Checkbutton(
            mode_selection_frame,
            text="Move Folders (direct)",
            variable=self.is_folder_mode,
            command=lambda: self.set_mode(self.is_folder_mode)
        )
        self.folder_checkbox.pack(side="left", padx=5)

        self.selective_checkbox = tk.Checkbutton(
            mode_selection_frame,
            text="Selective Folder/File Move",
            variable=self.is_selective_mode,
            command=lambda: self.set_mode(self.is_selective_mode)
        )
        self.selective_checkbox.pack(side="left", padx=5)


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
        # Initially set to disabled, will be enabled by execute_move
        self.log_text_area.config(state='disabled')

    def set_mode(self, mode_var_to_set):
        """Ensures mutual exclusivity of the mode checkboxes."""
        # Uncheck all other modes
        if mode_var_to_set != self.is_file_mode:
            self.is_file_mode.set(False)
        if mode_var_to_set != self.is_folder_mode:
            self.is_folder_mode.set(False)
        if mode_var_to_set != self.is_selective_mode:
            self.is_selective_mode.set(False)

        # Set the clicked mode to True
        mode_var_to_set.set(True)
        self.update_filenames_label() # Update the label based on the new mode

    def update_filenames_label(self):
        """Updates the label of the items list based on the active mode."""
        if self.is_file_mode.get():
            self.files_frame_label.config(text="Files to Move (one per line, with extension)")
        elif self.is_folder_mode.get():
            self.files_frame_label.config(text="Folders to Move (one per line)")
        elif self.is_selective_mode.get():
            self.files_frame_label.config(text="Selective Move: Folder then Files (e.g., folder1\\nfile1.txt\\nfile2.txt\\nfolder2\\n...)")
        else:
            # This case should ideally not be reached if one mode is always selected
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

        # Clear previous log output and enable logging for the duration of the operation
        self.log_text_area.config(state='normal')
        self.log_text_area.delete("1.0", tk.END)

        if not source_folder or not destination_folder:
            print("Warning: Please select both source and destination folders.\n")
            self.log_text_area.config(state='disabled') # Re-disable if early exit
            return

        original_stdout = sys.stdout
        sys.stdout = TextWidgetRedirector(self.log_text_area)

        try:
            if self.is_file_mode.get():
                move_items_simple(source_folder, item_names_list_str, destination_folder, False) # False for file mode
            elif self.is_folder_mode.get():
                move_items_simple(source_folder, item_names_list_str, destination_folder, True) # True for folder mode
            elif self.is_selective_mode.get():
                selective_move_logic(source_folder, item_names_list_str, destination_folder)
            else:
                print("Warning: Please select an operation mode (File, Folder, or Selective Move).\n")

        finally:
            # Restore original stdout
            sys.stdout = original_stdout
            # Disable logging area after the operation is complete
            self.log_text_area.config(state='disabled')


if __name__ == "__main__":
    root = tk.Tk()
    app = FileMoverApp(root)
    root.mainloop()
