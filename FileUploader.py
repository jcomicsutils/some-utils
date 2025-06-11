import tkinter as tk
from tkinter import filedialog, ttk
import os
import requests
import threading
import queue
import time
import subprocess
import re
import platform
import json
import tkinter.font

# ========== CONFIGURE THESE VALUES ==========
ACCOUNT_ID = ""
API_KEY = ""
CATBOX_USERHASH = ""
MAX_RETRIES = 20
RETRY_DELAY = 0.5  # seconds between retries
# ============================================

# Service size limits in bytes
SIZE_LIMITS = {
    'catbox': 200 * 1024 * 1024,        # 200MB
    'lain.la': 1 * 1024 * 1024 * 1024,    # 1GB
    'fileditch': 5 * 1024 * 1024 * 1024,  # 5GB
    'files.vc': 10 * 1024 * 1024 * 1024   # 10GB
}

class FileUploaderApp:
    def __init__(self, root):
        root.geometry("1200x900")  
        self.root = root
        self.root.title("Multi-Service File Uploader")
        self.root.configure(bg="#1e1e1e")
        self.service_queues = {
            'files.vc': queue.Queue(),
            'fileditch': queue.Queue(),
            'lain.la': queue.Queue(),
            'catbox': queue.Queue()
        }
        self.error_queue = queue.Queue()
        self.upload_queue = queue.Queue()
        self.consolidated_queue = queue.Queue()
        self.max_workers_var = tk.IntVar(value=10)
        self.services = {
            'files.vc': tk.BooleanVar(value=True),
            'fileditch': tk.BooleanVar(value=True),
            'lain.la': tk.BooleanVar(value=True),
            'catbox': tk.BooleanVar(value=True)
        }
        self.service_frames = {}
        self.consolidated_links = {}
        self.consolidated_lock = threading.Lock()
        self.save_log_var = tk.BooleanVar(value=False)

        if not ACCOUNT_ID or not API_KEY:
            raise ValueError("Account ID and API Key must be configured in the code")
        
        self.apply_dark_theme()        
        self.create_widgets()
        self.root.after(100, self.update_logs)

    def apply_dark_theme(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        dark_bg = "#1e1e1e"
        dark_fg = "#ffffff"
        dark_frame_bg = "#2e2e2e"
        dark_button_bg = "#3e3e3e"
        
        style.configure(".", background=dark_bg, foreground=dark_fg)
        style.configure("TFrame", background=dark_bg)
        style.configure("TLabel", background=dark_bg, foreground=dark_fg)
        style.configure("TLabelFrame", background=dark_frame_bg, foreground=dark_fg)
        style.configure("TLabelframe.Label", background=dark_bg, foreground=dark_fg)
        style.configure("TButton", background=dark_button_bg, foreground=dark_fg)
        style.map("TButton", background=[("active", dark_frame_bg)])
        style.configure("TCheckbutton", background=dark_bg, foreground=dark_fg)
        style.configure("TSpinbox",
            fieldbackground="#2e2e2e",
            background="#2e2e2e",
            foreground="#ffffff",
            insertcolor="#ffffff"
        )
        style.map("TSpinbox", background=[("readonly", "#2e2e2e")])
        
    def create_widgets(self):
        service_frame = ttk.LabelFrame(self.root, text="Services")
        service_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        
        for i, (name, var) in enumerate(self.services.items()):
            cb = ttk.Checkbutton(service_frame, text=name, variable=var)
            cb.grid(row=0, column=i, padx=5, pady=2)

        self.folder_btn = ttk.Button(self.root, text="Select Folder", command=self.select_folder)
        self.folder_btn.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.folder_label = ttk.Label(self.root, text="No folder selected")
        self.folder_label.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        self.upload_btn = ttk.Button(button_frame, text="Start Upload", command=self.start_upload)
        self.upload_btn.pack(side=tk.LEFT, padx=5)
        self.clear_btn = ttk.Button(button_frame, text="Clear Output", command=self.clear_output)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        self.save_log_check = ttk.Checkbutton(button_frame, text="Save Logs to File", variable=self.save_log_var)
        self.save_log_check.pack(side=tk.RIGHT, padx=5)

        left_btn_frame = ttk.Frame(button_frame)
        left_btn_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(left_btn_frame, text="Max Concurrent:").pack(side=tk.LEFT, padx=5)
        self.max_workers_spin = ttk.Spinbox(
            left_btn_frame, from_=1, to=50, width=4, textvariable=self.max_workers_var
        )
        self.max_workers_spin.pack(side=tk.LEFT, padx=5)

        service_panels = ttk.Frame(self.root)
        service_panels.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)

        for i, service in enumerate(self.services.keys()):
            frame = ttk.LabelFrame(service_panels, text=f"{service} Uploads")
            frame.grid(row=i//2, column=i%2, padx=5, pady=5, sticky=tk.NSEW)
            
            text_widget = tk.Text(frame, height=8, state=tk.DISABLED, bg="#2e2e2e", fg="#ffffff", insertbackground="#ffffff")
            text_widget.pack(fill=tk.BOTH, expand=True)
            
            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            text_widget['yscrollcommand'] = scrollbar.set
            
            self.service_frames[service] = text_widget

        consolidated_frame = ttk.LabelFrame(self.root, text="Consolidated Links")
        consolidated_frame.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)
        self.consolidated_text = tk.Text(consolidated_frame, height=8, state=tk.DISABLED, bg="#2e2e2e", fg="#ffffff", insertbackground="#ffffff")
        self.consolidated_text.pack(fill=tk.BOTH, expand=True)
        
        default_font = tkinter.font.nametofont(self.consolidated_text.cget("font"))
        bold_font = default_font.copy()
        bold_font.configure(weight="bold")
        self.consolidated_text.tag_configure("bold", font=bold_font, foreground="#ffffff", background="#000000")
        
        consolidated_scrollbar = ttk.Scrollbar(consolidated_frame, orient=tk.VERTICAL, command=self.consolidated_text.yview)
        consolidated_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.consolidated_text['yscrollcommand'] = consolidated_scrollbar.set

        error_frame = ttk.LabelFrame(self.root, text="Errors and Retries")
        error_frame.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)
        self.error_text = tk.Text(error_frame, height=8, state=tk.DISABLED, bg="#2e2e2e", fg="#ffffff", insertbackground="#ffffff")
        self.error_text.pack(fill=tk.BOTH, expand=True)
        error_scrollbar = ttk.Scrollbar(error_frame, orient=tk.VERTICAL, command=self.error_text.yview)
        error_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.error_text['yscrollcommand'] = error_scrollbar.set

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(3, weight=1)
        self.root.grid_rowconfigure(4, weight=1)
        service_panels.grid_columnconfigure(0, weight=1)
        service_panels.grid_columnconfigure(1, weight=1)

    def clear_output(self):
        for service, widget in self.service_frames.items():
            widget.config(state=tk.NORMAL)
            widget.delete(1.0, tk.END)
            widget.config(state=tk.DISABLED)
        self.error_text.config(state=tk.NORMAL)
        self.error_text.delete(1.0, tk.END)
        self.error_text.config(state=tk.DISABLED)
        self.consolidated_text.config(state=tk.NORMAL)
        self.consolidated_text.delete(1.0, tk.END)
        self.consolidated_text.config(state=tk.DISABLED)
        with self.consolidated_lock:
            self.consolidated_links.clear()

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_label.config(text=folder)

    def start_upload(self):
        folder_path = self.folder_label.cget("text")
        if folder_path == "No folder selected":
            self.error_queue.put("ERROR: Please select a folder first")
            return
        try:
            max_workers = int(self.max_workers_var.get())
            if max_workers < 1: raise ValueError
        except ValueError:
            self.error_queue.put("Invalid concurrent files value. Using default 10.")
            max_workers = 10

        self.upload_btn.config(state=tk.DISABLED)
        threading.Thread(
            target=self.prepare_upload,
            args=(folder_path, max_workers),
            daemon=True
        ).start()

    def prepare_upload(self, folder_path, max_workers):
        try:
            files = [os.path.join(folder_path, f) 
                    for f in os.listdir(folder_path)
                    if os.path.isfile(os.path.join(folder_path, f))]
            
            for file_path in files:
                self.upload_queue.put(file_path)
            
            workers = []
            for _ in range(min(max_workers, len(files))):
                worker = threading.Thread(
                    target=self.upload_worker,
                    daemon=True
                )
                worker.start()
                workers.append(worker)
            
            self.upload_queue.join()
            
        except Exception as e:
            self.error_queue.put(f"Preparation Error: {str(e)}")
        finally:
            self.root.after(0, lambda: self.upload_btn.config(state=tk.NORMAL))
            self.error_queue.put("Upload process completed")

    def upload_worker(self):
        while True:
            try:
                file_path = self.upload_queue.get_nowait()
            except queue.Empty:
                break
            
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            for service, var in self.services.items():
                if var.get():
                    if file_size > SIZE_LIMITS[service]:
                        self.error_queue.put(
                            f"[{service}] Skipped {filename} (File too large: {self.format_size(file_size)} > {self.format_size(SIZE_LIMITS[service])})"
                        )
                        continue
                        
                    try:
                        if service == 'files.vc':
                            self.handle_filesvc(file_path)
                        elif service == 'fileditch':
                            self.handle_fileditch(file_path)
                        elif service == 'lain.la':
                            self.handle_lainla(file_path)
                        elif service == 'catbox':
                            self.handle_catbox(file_path)
                    except Exception as e:
                        self.error_queue.put(f"[{service}] {filename}: {str(e)}")
            
            ordered_services = ['lain.la', 'catbox', 'fileditch', 'files.vc']
            links = []
            for service in ordered_services:
                if self.services[service].get():
                    with self.consolidated_lock:
                        if filename in self.consolidated_links and service in self.consolidated_links[filename]:
                            links.append(f'"{self.consolidated_links[filename][service]}"')
            
            if links:
                consolidated_line = f"{filename}: {', '.join(links)}"
                self.consolidated_queue.put(consolidated_line)
            
            self.upload_queue.task_done()

    def format_size(self, size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    def handle_filesvc(self, file_path):
        filename = os.path.basename(file_path)
        for attempt in range(MAX_RETRIES + 1):
            try:
                with open(file_path, 'rb') as f:
                    response = requests.post(
                        'https://api.files.vc/upload',
                        files={'file': (filename, f)},
                        headers={
                            'X-Account-ID': ACCOUNT_ID,
                            'X-API-Key': API_KEY
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                    debug_info = data.get('debug_info', {})
                    link = f"https://files.vc/d/dl?hash={debug_info.get('hash', '')}"
                    self.service_queues['files.vc'].put(f"{filename}: {link}")
                    with self.consolidated_lock:
                        if filename not in self.consolidated_links:
                            self.consolidated_links[filename] = {}
                        self.consolidated_links[filename]['files.vc'] = link
                    return
            except Exception as e:
                self.handle_retry('files.vc', filename, attempt, e)

    def handle_fileditch(self, file_path):
        filename = os.path.basename(file_path)
        for attempt in range(MAX_RETRIES + 1):
            try:
                if platform.system() == "Windows":
                    wsl_path = subprocess.check_output(
                        ['wsl', 'wslpath', '-a', file_path], 
                        text=True,
                        encoding='utf-8'
                    ).strip()
                    
                    result = subprocess.run(
                        ['wsl', 'curl', '-sS', '-H', 'Expect:', '-F', f'files[]=@"{wsl_path}"', 
                        'https://up1.fileditch.com/upload.php'],
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='replace',
                        check=True
                    )
                    raw_response = result.stdout
                else:
                    with open(file_path, 'rb') as f:
                        response = requests.post(
                            'https://up1.fileditch.com/upload.php',
                            files={'files[]': (filename, f)}
                        )
                        raw_response = response.text

                try:
                    raw_response = raw_response.encode('utf-8', 'replace').decode('utf-8', 'replace')
                except AttributeError:
                    pass

                if raw_response.startswith('HTTP/'):
                    try:
                        headers, body = raw_response.split('\n\n', 1)
                        raw_response = body
                    except ValueError:
                        pass

                response_data = json.loads(raw_response)
                
                if response_data.get('success') and response_data.get('files'):
                    first_file = response_data['files'][0]
                    clean_url = first_file['url'].replace('\\/', '/')
                    self.service_queues['fileditch'].put(f"{filename}: {clean_url}")
                    with self.consolidated_lock:
                        if filename not in self.consolidated_links:
                            self.consolidated_links[filename] = {}
                        self.consolidated_links[filename]['fileditch'] = clean_url
                    return
                else:
                    raise ValueError("Invalid response structure")
                
            except json.JSONDecodeError as e:
                error_msg = f"JSON parsing failed. First 500 chars: {raw_response[:500]}..."
                self.handle_retry('fileditch', filename, attempt, error_msg)
            except Exception as e:
                self.handle_retry('fileditch', filename, attempt, str(e))

    def handle_lainla(self, file_path):
        filename = os.path.basename(file_path)
        for attempt in range(MAX_RETRIES + 1):
            try:
                result = subprocess.run(
                    ['lain-upload', file_path],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                url_match = re.search(r'https?://[^\s]+', result.stdout)
                if url_match:
                    url = url_match.group()
                    self.service_queues['lain.la'].put(f"{filename}: {url}")
                    with self.consolidated_lock:
                        if filename not in self.consolidated_links:
                            self.consolidated_links[filename] = {}
                        self.consolidated_links[filename]['lain.la'] = url
                    return
                else:
                    raise ValueError("No URL found in output")
            except Exception as e:
                self.handle_retry('lain.la', filename, attempt, str(e))

    def handle_catbox(self, file_path):
        filename = os.path.basename(file_path)
        for attempt in range(MAX_RETRIES + 1):
            try:
                with open(file_path, 'rb') as f:
                    response = requests.post(
                        'https://catbox.moe/user/api.php',
                        files={
                            'reqtype': (None, 'fileupload'),
                            'userhash': (None, CATBOX_USERHASH),
                            'fileToUpload': (filename, f)
                        }
                    )
                    response.raise_for_status()
                    link = response.text.strip()
                    self.service_queues['catbox'].put(f"{filename}: {link}")
                    with self.consolidated_lock:
                        if filename not in self.consolidated_links:
                            self.consolidated_links[filename] = {}
                        self.consolidated_links[filename]['catbox'] = link
                    return
            except Exception as e:
                self.handle_retry('catbox', filename, attempt, str(e))

    def handle_retry(self, service, filename, attempt, error):
        if attempt < MAX_RETRIES:
            self.error_queue.put(
                f"[{service}] Retrying {filename} in {RETRY_DELAY}s (Attempt {attempt + 1}/{MAX_RETRIES})"
            )
            time.sleep(RETRY_DELAY)
        else:
            self.error_queue.put(f"[{service}] Failed to upload {filename}: {str(error)}")

    def update_logs(self):
        for service, q in self.service_queues.items():
            while not q.empty():
                msg = q.get_nowait()
                text_widget = self.service_frames[service]
                text_widget.config(state=tk.NORMAL)
                text_widget.insert(tk.END, msg + "\n")
                text_widget.config(state=tk.DISABLED)
                text_widget.see(tk.END)
        
        while not self.consolidated_queue.empty():
            msg = self.consolidated_queue.get_nowait()
            self.consolidated_text.config(state=tk.NORMAL)
            start_index = self.consolidated_text.index("end-1c")
            self.consolidated_text.insert(tk.END, msg + "\n")
            colon_pos = self.consolidated_text.search(":", start_index, stopindex=tk.END, exact=True, regexp=False)
            if colon_pos:
                self.consolidated_text.tag_add("bold", start_index, colon_pos)
            self.consolidated_text.config(state=tk.DISABLED)
            self.consolidated_text.see(tk.END)
        
        while not self.error_queue.empty():
            msg = self.error_queue.get_nowait()
            self.error_text.config(state=tk.NORMAL)
            self.error_text.insert(tk.END, msg + "\n")
            self.error_text.config(state=tk.DISABLED)
            self.error_text.see(tk.END)
        
        if self.save_log_var.get():
            self.save_logs_to_file()
        
        self.root.after(100, self.update_logs)

    def save_logs_to_file(self):
        log_content = "=== Service Logs ===\n"
        folder_path = self.folder_label.cget("text").rstrip("/").rsplit("/", 1)[-1]
        for service, widget in self.service_frames.items():
            log_content += f"[{service}]\n"
            content = widget.get("1.0", tk.END).strip()
            log_content += content + "\n\n"
        
        log_content += "\n=== Consolidated Links ===\n"
        consolidated_content = self.consolidated_text.get("1.0", tk.END).strip()
        log_content += consolidated_content + "\n\n"
        
        log_content += "\n=== Errors and Retries ===\n"
        error_content = self.error_text.get("1.0", tk.END).strip()
        log_content += error_content + "\n"
        
        try:
            with open(f"upload_log_{folder_path}.txt", "w", encoding="utf-8") as f:
                f.write(log_content)
        except Exception as e:
            self.error_queue.put(f"Error saving log file: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileUploaderApp(root)
    root.mainloop()