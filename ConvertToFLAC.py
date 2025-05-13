import os
import subprocess
from tkinter import Tk, filedialog, messagebox

def convert_audio_files(directory):
    """
    Converts all audio files in a directory to 44100Hz FLAC with compression level 12
    and deletes the original files after successful conversion.
    """
    if not os.path.isdir(directory):
        messagebox.showerror("Error", "The selected path is not a directory.")
        return

    # Supported extensions
    supported_extensions = (".mp3", ".wav", ".aac", ".ogg", ".m4a", ".wma", ".dsf")
    
    # Find all audio files in the directory
    audio_files = [
        os.path.join(directory, f) 
        for f in os.listdir(directory) 
        if f.lower().endswith(supported_extensions)
    ]

    if not audio_files:
        messagebox.showinfo("Info", "No supported audio files found in the selected directory.")
        return

    for file in audio_files:
        try:
            # Prepare output file path
            base_name = os.path.splitext(os.path.basename(file))[0]
            output_file = os.path.join(directory, f"{base_name}.flac")

            # ffmpeg command
            command = [
                "ffmpeg",
                "-i", file,
                "-ar", "44100",
                "-compression_level", "12",
                output_file
            ]
            
            # Run the ffmpeg command
            subprocess.run(command, check=True)
            
            # Remove the original file after successful conversion
            os.remove(file)
            print(f"Converted and deleted: {file}")

        except subprocess.CalledProcessError as e:
            print(f"Error converting file {file}: {e}")
        except Exception as e:
            print(f"Unexpected error with file {file}: {e}")

    messagebox.showinfo("Done", "All audio files have been converted.")

def select_directory():
    """
    Opens a directory selection dialog and starts the conversion process.
    """
    # Open a directory selection dialog
    directory = filedialog.askdirectory(title="Select a Directory")
    if directory:
        convert_audio_files(directory)

def main():
    """
    Main function to create the GUI and handle user interaction.
    """
    # Create the main Tkinter window
    root = Tk()
    root.withdraw()  # Hide the root window
    
    # Prompt user to select a directory
    select_directory()

if __name__ == "__main__":
    main()