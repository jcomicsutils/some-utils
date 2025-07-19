import os
import subprocess
import threading
import queue
from tkinter import *
from tkinter import filedialog, messagebox, ttk

def mix_audio_files(directory, status_queue=None):
    try:
        audio_files = [os.path.join(directory, f) for f in os.listdir(directory) 
                      if f.lower().endswith(('.mp3', '.wav', '.flac', '.aac'))]
        
        if not audio_files:
            if status_queue:
                status_queue.put(("status", f"No audio files found in {directory}"))
            return

        output_file = os.path.join(directory, "mixed_output.flac")
        input_args = []
        filter_complex = ""

        for idx, file in enumerate(audio_files):
            input_args.extend(["-i", file])
            filter_complex += f"[{idx}:a]"
        filter_complex += f"amix=inputs={len(audio_files)}[aout]"

        command = [
            "ffmpeg",
            *input_args,
            "-filter_complex", filter_complex,
            "-map", "[aout]",
            "-c:a", "flac",
            output_file
        ]

        subprocess.run(command, check=True, capture_output=True, text=True)

        # Remove original files after successful mix
        for file in audio_files:
            os.remove(file)

        if status_queue:
            status_queue.put(("status", f"Created {output_file} ({len(audio_files)} files merged)"))
            
    except subprocess.CalledProcessError as e:
        error_msg = f"FFmpeg error in {directory}: {e.stderr}"
        if status_queue:
            status_queue.put(("error", error_msg))
    except Exception as e:
        error_msg = f"Error in {directory}: {str(e)}"
        if status_queue:
            status_queue.put(("error", error_msg))

class AudioMergerGUI:
    def __init__(self, master):
        self.master = master
        master.title("Audio File Merger")
        
        # GUI Setup
        self.create_widgets()
        self.status_queue = queue.Queue()
        self.running = False
        self.master.after(100, self.process_queue)

    def create_widgets(self):
        # Directory Selection
        dir_frame = Frame(self.master)
        dir_frame.pack(padx=10, pady=10, fill=X)

        self.dir_label = Label(dir_frame, text="No directory selected")
        self.dir_label.pack(side=LEFT, expand=True, fill=X)

        browse_btn = Button(dir_frame, text="Browse", command=self.select_directory)
        browse_btn.pack(side=RIGHT)

        # Options
        options_frame = Frame(self.master)
        options_frame.pack(padx=10, pady=5, fill=X)
        
        self.subfolders_var = BooleanVar()
        Checkbutton(options_frame, text="Include Subfolders", variable=self.subfolders_var).pack(anchor=W)

        # Progress
        self.status_text = Text(self.master, height=12, state=DISABLED)
        self.status_text.pack(padx=10, pady=5, fill=BOTH, expand=True)

        # Start Button
        self.start_btn = Button(self.master, text="Start Merging", command=self.start_processing)
        self.start_btn.pack(pady=10)

    def select_directory(self):
        directory = filedialog.askdirectory(title="Select Root Directory")
        if directory:
            self.target_directory = directory
            self.dir_label.config(text=f"Selected: {directory}")

    def start_processing(self):
        if not hasattr(self, 'target_directory'):
            messagebox.showerror("Error", "Please select a directory first")
            return

        self.running = True
        self.start_btn.config(state=DISABLED)
        self.append_status("Starting processing...")
        
        processing_thread = threading.Thread(
            target=self.process_directories,
            args=(self.target_directory, self.subfolders_var.get()),
            daemon=True
        )
        processing_thread.start()

    def process_directories(self, root_dir, include_subfolders):
        try:
            if include_subfolders:
                for dirpath, _, _ in os.walk(root_dir):
                    self.status_queue.put(("status", f"Processing: {dirpath}"))
                    mix_audio_files(dirpath, self.status_queue)
            else:
                self.status_queue.put(("status", f"Processing: {root_dir}"))
                mix_audio_files(root_dir, self.status_queue)
                
            self.status_queue.put(("done", "Processing completed successfully!"))
        except Exception as e:
            self.status_queue.put(("error", str(e)))

    def append_status(self, message):
        self.status_text.config(state=NORMAL)
        self.status_text.insert(END, message + "\n")
        self.status_text.see(END)
        self.status_text.config(state=DISABLED)

    def process_queue(self):
        while not self.status_queue.empty():
            msg_type, content = self.status_queue.get()
            
            if msg_type == "status":
                self.append_status(content)
            elif msg_type == "error":
                self.append_status(f"ERROR: {content}")
                messagebox.showerror("Error", content)
            elif msg_type == "done":
                self.append_status(content)
                self.start_btn.config(state=NORMAL)
                self.running = False

        self.master.after(100, self.process_queue)

if __name__ == "__main__":
    root = Tk()
    app = AudioMergerGUI(root)
    root.mainloop()