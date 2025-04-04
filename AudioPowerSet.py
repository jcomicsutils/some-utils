import os
import re
import itertools
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk  # Import ttk for ProgressBar
import random  # Import random for shuffling

class AudioMixerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FLAC Audio Mixing Tool with Custom Naming")

        self.stop_mixing = False  # Control flag for stopping the mixing process
        self.mixing_thread = None  # Thread for the mixing process

        # Input directory selection
        tk.Label(root, text="Input Directory:").grid(row=0, column=0, padx=10, pady=10)
        self.input_dir_entry = tk.Entry(root, width=50)
        self.input_dir_entry.grid(row=0, column=1, padx=10, pady=10)
        tk.Button(root, text="Browse", command=self.browse_input_directory).grid(row=0, column=2, padx=10, pady=10)

        # Output directory selection
        tk.Label(root, text="Output Directory:").grid(row=1, column=0, padx=10, pady=10)
        self.output_dir_entry = tk.Entry(root, width=50)
        self.output_dir_entry.grid(row=1, column=1, padx=10, pady=10)
        tk.Button(root, text="Browse", command=self.browse_output_directory).grid(row=1, column=2, padx=10, pady=10)

        # Filename convention input
        tk.Label(root, text="Filename Convention:").grid(row=2, column=0, padx=10, pady=10)
        self.filename_convention_entry = tk.Entry(root, width=50)
        self.filename_convention_entry.grid(row=2, column=1, padx=10, pady=10)
        self.filename_convention_entry.insert(0, "[filename1][filename2]")  # Default convention

        # Buttons to start and stop mixing
        self.start_button = tk.Button(root, text="Start Mixing", command=self.run_stitching_process)
        self.start_button.grid(row=3, column=0, padx=10, pady=20)
        self.stop_button = tk.Button(root, text="Stop Mixing", command=self.stop_stitching_process)
        self.stop_button.grid(row=3, column=2, padx=10, pady=20)

        # Progress bar and status
        self.progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.grid(row=4, column=1, padx=10, pady=10)
        self.progress_label = tk.Label(root, text="Progress: 0 of 0")
        self.progress_label.grid(row=4, column=0, padx=10, pady=10)

    def browse_input_directory(self):
        """Open file dialog to select input directory."""
        directory = filedialog.askdirectory()
        if directory:
            self.input_dir_entry.delete(0, tk.END)
            self.input_dir_entry.insert(0, directory)

    def browse_output_directory(self):
        """Open file dialog to select output directory."""
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, directory)

    def clean_filename(self, filename):
        """Remove strings of the form 'n - ' from the filename."""
        return re.sub(r'\d+ - ', '', filename)

    def generate_output_filename(self, combo, convention):
        """
        Generate an output filename based on the selected naming convention.
        Args:
            combo (list): List of file paths in the combination.
            convention (str): The chosen filename convention.
        Returns:
            str: The generated filename.
        """
        base_filenames = [self.clean_filename(os.path.basename(f).split('.')[0]) for f in combo]
        random.shuffle(base_filenames)  # Shuffle the filenames
        if convention == "[filename1][filename2]":
            return f"{''.join(base_filenames)}.flac"
        else:
            return "_".join(base_filenames) + ".flac"

    def stop_stitching_process(self):
        """Set the stop flag to True."""
        self.stop_mixing = True
        messagebox.showinfo("Stopping", "Stopping the mixing process...")

    def stitch_audio_files_simultaneously(self, directory, output_dir, convention):
        """Combine all audio files in the given directory to play simultaneously."""
        self.stop_mixing = False
        os.makedirs(output_dir, exist_ok=True)
        files = [os.path.join(directory, f) for f in os.listdir(directory)
                 if os.path.isfile(os.path.join(directory, f)) and self.is_audio_file(f)]

        if not files:
            messagebox.showerror("Error", "No audio files found in the directory.")
            return

        # Calculate total combinations
        total_combinations = sum(1 for r in range(2, len(files) + 1) for _ in itertools.combinations(files, r))
        self.progress_bar["maximum"] = total_combinations
        self.progress_bar["value"] = 0
        self.progress_label.config(text=f"Progress: 0 of {total_combinations}")

        processed_count = 0
        for r in range(2, len(files) + 1):
            for combo in itertools.combinations(files, r):
                if self.stop_mixing:
                    print("Mixing process stopped.")
                    return

                inputs = " ".join([f"-i \"{file}\"" for file in combo])
                filter_complex = "".join([f"[{i}:a:0]" for i in range(len(combo))])
                filter_complex += f"amix=inputs={len(combo)}[a]"
                output_file = os.path.join(output_dir, self.generate_output_filename(combo, convention))

                ffmpeg_command = (
                    f"ffmpeg {inputs} -filter_complex \"{filter_complex}\" "
                    f"-map \"[a]\" -c:a flac -compression_level 12 -y \"{output_file}\""
                )

                try:
                    subprocess.run(ffmpeg_command, shell=True, check=True)
                    print(f"Successfully created: {output_file}")
                except subprocess.CalledProcessError as e:
                    print(f"Error processing combination {combo}: {e}")

                processed_count += 1
                self.progress_bar["value"] = processed_count
                self.progress_label.config(text=f"Progress: {processed_count} of {total_combinations}")
                self.root.update_idletasks()

        if not self.stop_mixing:
            messagebox.showinfo("Success", "All audio combinations have been processed successfully.")

    def is_audio_file(self, file):
        """Check if a file has an audio extension."""
        audio_extensions = ('.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a')
        return file.lower().endswith(audio_extensions)

    def run_stitching_process(self):
        """Run the stitching process in a separate thread."""
        input_dir = self.input_dir_entry.get()
        output_dir = self.output_dir_entry.get()
        convention = self.filename_convention_entry.get()

        if not input_dir or not output_dir:
            messagebox.showerror("Error", "Please specify both input and output directories.")
            return

        if not os.path.exists(input_dir):
            messagebox.showerror("Error", "The input directory does not exist.")
            return

        if not os.path.exists(output_dir):
            messagebox.showerror("Error", "The output directory does not exist.")
            return

        # Start the stitching process in a separate thread
        self.mixing_thread = threading.Thread(
            target=self.stitch_audio_files_simultaneously,
            args=(input_dir, output_dir, convention),
            daemon=True
        )
        self.mixing_thread.start()


# Run the GUI
root = tk.Tk()
app = AudioMixerApp(root)
root.mainloop()
