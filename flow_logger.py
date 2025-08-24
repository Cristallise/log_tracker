import csv
import os
import sys
import uuid
from datetime import datetime, timezone
import threading

# GUI
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ImportError:
    print("tkinter not found. On some Linux systems install: sudo apt-get install python3-tk")
    sys.exit(1)

# Global hotkey
from pynput import keyboard

SCHEMA_VERSION = 1
LOG_FILE = "flow_log.csv"

# In-memory open session (None if no session open)
open_session_id = None
open_session_started_at = None

# Simple app/window capture stubs (kept minimal for portability)
def get_active_app_and_title():
    # Cross-platform active window detection can be added later.
    # For now, return empty strings so CSV stays consistent.
    return "", ""

def iso_now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def ensure_csv_header(path):
    exists = os.path.exists(path)
    if not exists:
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "log_id","timestamp","event","session_id",
                "action_note","tags","app_name","window_title","url","schema_version"
            ])

def write_row(event, session_id, note, tags, app_name, window_title, url=""):
    ensure_csv_header(LOG_FILE)
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            str(uuid.uuid4()),
            iso_now(),
            event,
            session_id or "",
            note or "",
            tags or "",
            app_name or "",
            window_title or "",
            url or "",
            SCHEMA_VERSION
        ])

class FlowPopup(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.title("Flow Logger")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        # Layout
        pad = {"padx": 10, "pady": 6}
        row = 0

        # Previous session banner
        self.stop_prev_var = tk.BooleanVar(value=True)  # default = checked
        self.promote_note_var = tk.BooleanVar(value=False)  # for standalone notes

        banner_text = ""
        if open_session_id is not None:
            started_str = open_session_started_at.strftime("%I:%M %p").lstrip("0")
            banner_text = f"Previous session open • Started {started_str}"

        if banner_text:
            ttk.Label(self, text=banner_text).grid(row=row, column=0, columnspan=3, sticky="w", **pad); row+=1
            ttk.Checkbutton(self, text="Stop that session when I save",
                            variable=self.stop_prev_var).grid(row=row, column=0, columnspan=3, sticky="w", **pad); row+=1

        # What are you doing?
        ttk.Label(self, text="What are you doing?").grid(row=row, column=0, sticky="w", **pad)
        self.note_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.note_var, width=44).grid(row=row, column=1, columnspan=2, sticky="we", **pad); row+=1

        # Quick tags (simple comma field for v1)
        ttk.Label(self, text="Tags (comma-separated)").grid(row=row, column=0, sticky="w", **pad)
        self.tags_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.tags_var, width=44).grid(row=row, column=1, columnspan=2, sticky="we", **pad); row+=1

        # Context (read-only)
        app_name, window_title = get_active_app_and_title()
        self.app_name = app_name
        self.window_title = window_title
        ttk.Label(self, text=f"App: {app_name or '—'}").grid(row=row, column=0, columnspan=3, sticky="w", **pad); row+=1
        ttk.Label(self, text=f"Title: {window_title or '—'}").grid(row=row, column=0, columnspan=3, sticky="w", **pad); row+=1

        # Buttons
        self.event_var = tk.StringVar(value="start")
        btns = ttk.Frame(self)
        btns.grid(row=row, column=0, columnspan=3, sticky="we", **pad); row+=1

        ttk.Radiobutton(btns, text="Start", value="start", variable=self.event_var).grid(row=0, column=0, padx=6)
        ttk.Radiobutton(btns, text="Note", value="note", variable=self.event_var).grid(row=0, column=1, padx=6)
        ttk.Radiobutton(btns, text="Stop", value="stop", variable=self.event_var).grid(row=0, column=2, padx=6)

        # Only show "promote note" when no session is open and event=note
        self.promote_chk = ttk.Checkbutton(self, text="Make this note a new session start",
                                           variable=self.promote_note_var)
        if open_session_id is None and self.event_var.get() == "note":
            self.promote_chk.grid(row=row, column=0, columnspan=3, sticky="w", **pad)
        self.event_var.trace_add("write", self._toggle_promote)
        row += 1

        save_btn = ttk.Button(self, text="Save", command=self.on_save)
        save_btn.grid(row=row, column=2, sticky="e", **pad)
        self.bind("<Return>", lambda _: self.on_save())

    def _toggle_promote(self, *_):
        if open_session_id is None and self.event_var.get() == "note":
            if not hasattr(self.promote_chk, "winfo_ismapped") or not self.promote_chk.winfo_ismapped():
                self.promote_chk.grid()
        else:
            try:
                self.promote_chk.grid_remove()
            except Exception:
                pass

    def on_save(self):
        global open_session_id, open_session_started_at

        note = self.note_var.get().strip()
        tags = self.tags_var.get().strip()
        event = self.event_var.get()
        app_name = self.app_name
        window_title = self.window_title

        # If a session is open and box checked: write a stop row first
        if open_session_id and self.stop_prev_var.get():
            write_row(
                event="stop",
                session_id=open_session_id,
                note="(auto-stop)",
                tags="",
                app_name=app_name,
                window_title=window_title,
                url=""
            )
            open_session_id = None
            open_session_started_at = None

        # Determine target session for this new entry
        target_session = open_session_id

        if event == "start":
            # Start a brand new session
            target_session = str(uuid.uuid4())
            open_session_id = target_session
            open_session_started_at = datetime.now()

        elif event == "note":
            if open_session_id is None:
                # Standalone note by default
                target_session = ""
                # Optionally promote to new session
                if self.promote_note_var.get():
                    target_session = str(uuid.uuid4())
                    open_session_id = target_session
                    open_session_started_at = datetime.now()

        elif event == "stop":
            # If no session open, just write a stop row unattached
            target_session = open_session_id or ""

            # If stopping, clear open session after writing below
        else:
            event = "note"

        write_row(
            event=event,
            session_id=target_session,
            note=note,
            tags=tags,
            app_name=app_name,
            window_title=window_title,
            url=""
        )

        # If user explicitly chose Stop, close session
        if event == "stop" and open_session_id:
            open_session_id = None
            open_session_started_at = None

        # Tiny toast
        try:
            self.after(10, lambda: messagebox.showinfo("Flow Logger", "Saved"))
        except Exception:
            pass

        self.destroy()

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # hide root window

        # Start global hotkey listener in a thread
        self.listener_thread = threading.Thread(target=self._hotkey_listener, daemon=True)
        self.listener_thread.start()

        # Also let user click the tray-less app window with Ctrl+L fallback
        self.root.bind_all("<Control-l>", lambda e: self.open_popup())

    def _hotkey_listener(self):
        # Ctrl+Alt+L (Win/Linux) or Cmd+Opt+L (macOS) handled by modifier alternatives
        COMBO_WIN = {keyboard.Key.ctrl_l, keyboard.Key.alt_l, keyboard.KeyCode.from_char('l')}
        COMBO_MAC = {keyboard.Key.cmd, keyboard.Key.alt, keyboard.KeyCode.from_char('l')}
        current_keys = set()

        def on_press(key):
            current_keys.add(key)
            if COMBO_WIN.issubset(current_keys) or COMBO_MAC.issubset(current_keys):
                # Open popup on the Tk mainloop thread
                self.root.after(0, self.open_popup)

        def on_release(key):
            if key in current_keys:
                current_keys.remove(key)

        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()

    def open_popup(self):
        # Only one popup at a time
        if any(isinstance(w, FlowPopup) for w in self.root.winfo_children()):
            return
        FlowPopup(self.root)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    App().run()
