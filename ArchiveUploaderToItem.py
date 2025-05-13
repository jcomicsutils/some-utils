import tkinter as tk
from tkinter import ttk, messagebox
import os
import threading
import queue
import time
import re
from pathlib import Path
from internetarchive import upload, get_item
from tkfilebrowser import askopendirnames

# Drag-and-drop support
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    dnd_available = True
except ImportError:
    dnd_available = False

# ========== CONFIGURE THESE VALUES ==========
IA_ACCESS_KEY = ""
IA_SECRET_KEY = ""
IA_METADATA = {
    'collection': 'opensource',
    'mediatype': 'data',
}
MAX_RETRIES = 5
RETRY_DELAY = 1   # seconds between retries
SIZE_LIMITS = {'internetarchive': 1024 ** 4}  # 1TB
# ============================================

def tkfilebrowser_dark_style():
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Treeview",
                    background="#2d2d2d",
                    foreground="#ffffff",
                    fieldbackground="#2d2d2d",
                    bordercolor="#444444")
    style.map("Treeview",
              background=[('selected', '#4d4d4d')],
              foreground=[('selected', '#ffffff')])
    style.configure("TEntry",
                    fieldbackground="#2d2d2d",
                    foreground="#ffffff")

class FileUploaderApp:
    def __init__(self, root):
        root.geometry("1200x900")
        self.root = root
        self.root.title("archive.org File Uploader")
        self.root.configure(bg="#1e1e1e")

        self.folder_paths       = []
        self.upload_queue       = queue.Queue()
        self.error_queue        = queue.Queue()
        self.service_queues     = {s: queue.Queue() for s in SIZE_LIMITS}
        self.upload_lock        = threading.Lock()
        self.concurrency        = 1
        self.services           = {s: tk.BooleanVar(value=True) for s in SIZE_LIMITS}
        self.include_subfolders = tk.BooleanVar(value=True)

        self.use_existing_item     = tk.BooleanVar(value=True)
        self.existing_identifier   = tk.StringVar()

        self.service_frames     = {}

        self.apply_dark_theme()
        self.create_widgets()
        self.root.after(100, self.update_logs)

    def apply_dark_theme(self):
        s = ttk.Style()
        s.theme_use('clam')
        s.configure(".",          background="#1e1e1e", foreground="#ffffff")
        s.configure("TFrame",     background="#1e1e1e")
        s.configure("TLabel",     background="#1e1e1e", foreground="#ffffff")
        s.configure("TLabelFrame",background="#2e2e2e", foreground="#ffffff")
        s.configure("TButton",    background="#3e3e3e", foreground="#ffffff")
        s.map("TButton",          background=[("active","#2e2e2e")])
        s.configure("TCheckbutton",background="#1e1e1e", foreground="#ffffff")

    def create_widgets(self):
        # Services + subfolder toggle
        svc_frame = ttk.LabelFrame(self.root, text="Services")
        svc_frame.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky=tk.EW)
        for i,(name,var) in enumerate(self.services.items()):
            ttk.Checkbutton(svc_frame, text=name, variable=var).grid(row=0, column=i, padx=5)
        ttk.Checkbutton(svc_frame, text="Include Subfolders", variable=self.include_subfolders)\
            .grid(row=0, column=len(self.services), padx=20)

        # Folder selection & drag-drop
        ctl = ttk.Frame(self.root)
        ctl.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=tk.EW)
        ttk.Button(ctl, text="Select Folders", command=self.select_folders).pack(side=tk.LEFT)
        ttk.Button(ctl, text="Remove All",     command=self.clear_folders).pack(side=tk.LEFT, padx=5)

        self.folder_listbox = tk.Listbox(self.root,
                                         height=6,
                                         bg="#2e2e2e",
                                         fg="#ffffff",
                                         selectbackground="#4d4d4d")
        self.folder_listbox.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        if dnd_available:
            self.folder_listbox.drop_target_register(DND_FILES)
            self.folder_listbox.dnd_bind('<<Drop>>', self.handle_drop)

        # Upload controls
        btnf = ttk.Frame(self.root)
        btnf.grid(row=3, column=0, columnspan=3, pady=5, sticky=tk.EW)
        ttk.Label(btnf, text="Concurrent Uploads:").pack(side=tk.LEFT)
        self.concurrent_spinbox = tk.Spinbox(btnf, from_=1, to=10, width=5)
        self.concurrent_spinbox.pack(side=tk.LEFT, padx=5)
        self.concurrent_spinbox.delete(0,"end"); self.concurrent_spinbox.insert(0,"1")
        self.upload_btn = ttk.Button(btnf, text="Start Upload", command=self.start_upload)
        self.upload_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(btnf, text="Clear Output", command=self.clear_output).pack(side=tk.LEFT, padx=5)

        # Existing item option
        exist_frame = ttk.Frame(self.root)
        exist_frame.grid(row=3, column=3, padx=5, pady=5, sticky=tk.W)
        ttk.Checkbutton(exist_frame,
                        text="Upload to Existing Item",
                        variable=self.use_existing_item,
                        command=self.toggle_existing_entry).grid(row=0, column=0, sticky=tk.W)
        self.identifier_entry = ttk.Entry(exist_frame,
                                          textvariable=self.existing_identifier,
                                          width=40, foreground="#2e2e2e")
        # initially hidden
        self.identifier_entry.grid_remove()

        # Logs
        logf = ttk.Frame(self.root)
        logf.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        for i,svc in enumerate(self.services):
            f = ttk.LabelFrame(logf, text=f"{svc} Uploads")
            f.grid(row=i//2, column=i%2, padx=5, pady=5, sticky="nsew")
            tw = tk.Text(f, height=20, bg="#2e2e2e", fg="#ffffff",
                         state=tk.DISABLED, insertbackground="#ffffff")
            tw.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            sb = ttk.Scrollbar(f, orient=tk.VERTICAL, command=tw.yview)
            sb.pack(side=tk.RIGHT, fill=tk.Y); tw['yscrollcommand'] = sb.set
            self.service_frames[svc] = tw

        ef = ttk.LabelFrame(self.root, text="Errors and Retries")
        ef.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky=tk.NSEW)
        self.error_text = tk.Text(ef, height=6, bg="#2e2e2e", fg="#ffffff",
                                  state=tk.DISABLED, insertbackground="#ffffff")
        self.error_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        esb = ttk.Scrollbar(ef, orient=tk.VERTICAL, command=self.error_text.yview)
        esb.pack(side=tk.RIGHT, fill=tk.Y); self.error_text['yscrollcommand'] = esb.set

        # Layout weights
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_rowconfigure(4, weight=1)
        logf.grid_columnconfigure(0, weight=1)
        logf.grid_columnconfigure(1, weight=1)

    def toggle_existing_entry(self):
        if self.use_existing_item.get():
            self.identifier_entry.grid(row=1, column=0, pady=2, sticky=tk.W)
        else:
            self.identifier_entry.grid_remove()

    def clear_output(self):
        for tw in self.service_frames.values():
            tw.config(state=tk.NORMAL); tw.delete("1.0","end"); tw.config(state=tk.DISABLED)
        self.error_text.config(state=tk.NORMAL); self.error_text.delete("1.0","end"); self.error_text.config(state=tk.DISABLED)

    def clear_folders(self):
        self.folder_paths.clear()
        self.folder_listbox.delete(0, tk.END)

    def select_folders(self):
        tkfilebrowser_dark_style()
        paths = askopendirnames(title="Select Folders", initialdir=os.path.expanduser("~"))
        for p in paths:
            if os.path.isdir(p) and p not in self.folder_paths:
                self.folder_paths.append(p)
                self.folder_listbox.insert(tk.END, p)

    def handle_drop(self, event):
        for path in self.root.tk.splitlist(event.data):
            if os.path.isdir(path) and path not in self.folder_paths:
                self.folder_paths.append(path)
                self.folder_listbox.insert(tk.END, path)
            else:
                self.error_queue.put(f"Ignored non-folder: {path}")

    def start_upload(self):
        try:
            self.concurrency = int(self.concurrent_spinbox.get())
        except ValueError:
            self.concurrency = 1

        self.upload_btn.config(state=tk.DISABLED)
        for folder in self.folder_paths:
            self.upload_queue.put(folder)

        threading.Thread(target=self.watch_completion, daemon=True).start()
        for _ in range(self.concurrency):
            threading.Thread(target=self.upload_worker, daemon=True).start()

    def watch_completion(self):
        self.upload_queue.join()
        self.error_queue.put("Upload Process Completed")
        self.root.after(0, lambda: self.upload_btn.config(state=tk.NORMAL))

    def upload_worker(self):
        while True:
            try:
                folder = self.upload_queue.get_nowait()
            except queue.Empty:
                return

            # Prepare identifier and metadata
            base_dir    = os.path.dirname(folder)
            folder_name = os.path.basename(folder)
            safe_name   = re.sub(r'[^a-zA-Z0-9_-]', '_', folder_name).lower()[:50]

            if self.use_existing_item.get():
                identifier = self.existing_identifier.get().strip()
                metadata = None
            else:
                identifier = f"{int(time.time())}_{safe_name}"
                metadata = IA_METADATA.copy()
                metadata.update({'title': folder_name, 'identifier': identifier})

            prev_cwd = os.getcwd()
            os.chdir(base_dir)
            try:
                for attempt in range(MAX_RETRIES+1):
                    try:
                        resp = upload(
                            identifier,
                            folder_name,
                            metadata=metadata,
                            access_key=IA_ACCESS_KEY,
                            secret_key=IA_SECRET_KEY,
                            verbose=True
                        )
                        if all(r.status_code == 200 for r in resp):
                            msg = f"{folder_name}: https://archive.org/details/{identifier}"
                            self.service_queues['internetarchive'].put(msg)
                            break
                        else:
                            raise Exception("Directory upload failed")
                    except Exception as e:
                        if attempt >= MAX_RETRIES:
                            self.error_queue.put(f"{folder_name} failed: {e}")
                        else:
                            time.sleep(RETRY_DELAY)
            finally:
                os.chdir(prev_cwd)
                self.upload_queue.task_done()

    def update_logs(self):
        for svc, q in self.service_queues.items():
            while not q.empty():
                txt = q.get_nowait()
                tw  = self.service_frames[svc]
                tw.config(state=tk.NORMAL); tw.insert(tk.END, txt+"\n"); tw.see(tk.END); tw.config(state=tk.DISABLED)

        while not self.error_queue.empty():
            err = self.error_queue.get_nowait()
            self.error_text.config(state=tk.NORMAL); self.error_text.insert(tk.END, err+"\n"); self.error_text.see(tk.END); self.error_text.config(state=tk.DISABLED)

        self.root.after(100, self.update_logs)


if __name__ == "__main__":
    root = TkinterDnD.Tk() if dnd_available else tk.Tk()
    app = FileUploaderApp(root)
    root.mainloop()
