import os
import subprocess
from tkinter import filedialog, Tk, messagebox

def mix_audio_files(directory):
    try:
        # Find all audio files in the directory
        audio_files = [os.path.join(directory, file) for file in os.listdir(directory) if file.endswith(('.mp3', '.wav', '.flac', '.aac'))]

        if not audio_files:
            print("No audio files found in the selected directory.")
            return

        # Output mixed audio file name
        output_file = os.path.join(directory, "mixed_output.flac")

        # Prepare ffmpeg input arguments and filter_complex for amix
        input_args = []
        filter_complex = ""
        for idx, audio_file in enumerate(audio_files):
            input_args.extend(["-i", audio_file])
            filter_complex += f"[{idx}:a]"
        filter_complex += f"amix=inputs={len(audio_files)}[aout]"

        # Complete ffmpeg command
        command = [
            "ffmpeg",
            *input_args,
            "-filter_complex", filter_complex,
            "-map", "[aout]",
            "-c:a", "flac",
            output_file
        ]

        subprocess.run(command, check=True)

        # Delete the original audio files
        for audio_file in audio_files:
            os.remove(audio_file)

        print(f"Mixed audio file created: {output_file}")

    except subprocess.CalledProcessError as e:
        print(f"ffmpeg encountered an error: {e}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def main():
    # Hide the root Tkinter window
    root = Tk()
    root.withdraw()

    directory = filedialog.askdirectory(title="Select Directory Containing Audio Files")
    if directory:
        mix_audio_files(directory)

if __name__ == "__main__":
    main()