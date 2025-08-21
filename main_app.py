# main_app.py
import sys
import os
import time
from tkinterdnd2 import DND_FILES
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
from treeview_manager import TreeViewManager
from output_window import show_output_window
from config_manager import ConfigManager
from ui import UI
from scanner import scan_directory_fast
from generator import generate_text_content_fast
from settings_window import show_settings_window

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class DirectoryToTextApp:
    def __init__(self, root, verbose=False):
        self.root = root
        self.verbose = verbose
        self.config = ConfigManager()
        self.root_dir = tk.StringVar(value=self.config.get_setting('Settings', 'last_folder'))
        self._setup_window()
        self.scanned_tree_data = None # This will hold the complete scanned data structure

        callbacks = {
            'select_folder': self.select_folder,
            'check_selected': self.check_selected,
            'uncheck_selected': self.uncheck_selected,
            'check_all': self.check_all,
            'uncheck_all': self.uncheck_all,
            'start_conversion': self.start_conversion_thread,
            'cancel_operation': self.cancel_current_operation,
            'exit': self.on_closing,
            'show_about': self.show_about,
            'show_settings': self.show_settings,
        }
        self.ui = UI(self.root, callbacks, self.root_dir)
        self.ui.tree.tag_configure('ignored', foreground='gray')
        self.ignored_items = self.config.get_ignored_set()
        # Pass the resource_path function to the manager so it can find image assets
        self.tree_manager = TreeViewManager(self.ui.tree, self.root, self.log_message, self.ignored_items, resource_path)
        self._setup_event_bindings()

        self.scan_thread = None
        self.generation_thread = None
        self.cancel_scan = threading.Event()
        self.cancel_generation = threading.Event()
        self.operation_start_time = None

        if self.root_dir.get():
            self._load_folder(self.root_dir.get())

    def _setup_window(self):
        width = self.config.get_setting('Settings', 'width')
        height = self.config.get_setting('Settings', 'height')
        self.root.title("CodebaseToText v7.3") 
        self.root.geometry(f"{width}x{height}")
        theme = self.config.get_setting('Settings', 'theme')
        if theme not in ['dark', 'light']:
            theme = 'dark'
        azure_path = resource_path('azure.tcl')
        self.root.tk.call('source', azure_path)
        self.root.tk.call('set_theme', theme)

    def _setup_event_bindings(self):
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.handle_drop)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _load_folder(self, folder_path):
        if not os.path.isdir(folder_path):
            self.log_message(f"Attempted to load invalid path: {folder_path}")
            messagebox.showerror("Error", f"The selected path '{folder_path}' is not a valid directory.")
            return
            
        self.root_dir.set(folder_path)
        self.log_message(f"Scanning folder: {folder_path}")
        
        self.scanned_tree_data = None # Clear previous scan data
        self.tree_manager.clear_tree()
        self.ui.tree.insert("", "end", text="  Scanning and analyzing files, please wait...")
        
        self.ui.generate_button.config(state='disabled')
        self.ui.browse_button.config(state='disabled')
        self.ui.cancel_button.config(state='normal')
        self.operation_start_time = time.time()
        
        self.cancel_scan.clear()
        self.scan_thread = threading.Thread(
            target=self._scan_folder_thread_fast,
            args=(folder_path, self.cancel_scan),
            daemon=True
        )
        self.scan_thread.start()

    def _scan_folder_thread_fast(self, folder_path, cancel_event):
        """Worker function to scan directory in the background."""
        tree_data = None
        try:
            tree_data = scan_directory_fast(folder_path, self.ignored_items, cancel_event)
            if tree_data:
                self.scanned_tree_data = tree_data  # <-- STORE THE RESULT
                self.root.after(0, self._populate_tree_ui, tree_data)
        except Exception as e:
            self.log_message(f"Error scanning directory: {e}")
        finally:
            self.root.after(0, self._reset_ui_after_scan, (tree_data is None))

    def _populate_tree_ui(self, tree_data):
        """Callback to update the treeview on the main thread."""
        self.log_message("Scan complete. Populating UI.")
        self.tree_manager.populate_from_data(tree_data)

    def _reset_ui_after_scan(self, cancelled=False):
        """Resets the UI state after a scan finishes or is cancelled."""
        self.ui.cancel_button.config(state='disabled')
        self.ui.browse_button.config(state='normal')
        
        duration_message = ""
        if self.operation_start_time:
            duration = time.time() - self.operation_start_time
            duration_message = f" Finished in {duration:.2f} seconds."
            self.operation_start_time = None

        if cancelled:
            self.tree_manager.clear_tree()
            self.ui.tree.insert("", "end", text="  Scan cancelled by user.")
            self.log_message("Scan was cancelled.")
            self.update_status("Scan cancelled." + duration_message)
            self.ui.generate_button.config(state='disabled')
        else:
            self.update_status("Scan complete." + duration_message)
            self.ui.generate_button.config(state='normal')

    def select_folder(self):
        last_folder = self.config.get_setting('Settings', 'last_folder')
        folder_selected = filedialog.askdirectory(initialdir=last_folder if os.path.isdir(last_folder) else None)
        if folder_selected:
            self._load_folder(folder_selected)

    def handle_drop(self, event):
        if event.data:
            folder_path = event.data.strip()
            self._load_folder(folder_path)
    
    def start_conversion_thread(self):
        root_path = self.root_dir.get()
        if not self.scanned_tree_data:
            messagebox.showerror("Error", "No directory has been scanned successfully.")
            return

        files_for_content = self.tree_manager.get_checked_files()
        
        self.log_message("Starting generation...")
        self.ui.generate_button.config(state='disabled')
        self.ui.browse_button.config(state='disabled')
        self.ui.cancel_button.config(state='normal')
        self.update_status("Starting generation...")
        self.operation_start_time = time.time()
        
        self.ui.progress_bar['value'] = 0
        self.cancel_generation.clear()

        # This is now the fast path, directly using the scanned data.
        self.generation_thread = threading.Thread(
            target=generate_text_content_fast,
            args=(
                root_path, self.scanned_tree_data, files_for_content, 
                self.log_message, self._thread_safe_display_results, self._thread_safe_reset_after_generation,
                self.cancel_generation, self.update_status, self.update_progress
            ),
            daemon=True
        )
        self.generation_thread.start()

    def cancel_current_operation(self):
        if self.scan_thread and self.scan_thread.is_alive():
            self.log_message("Scan cancellation requested.")
            self.update_status("Cancelling scan...")
            self.cancel_scan.set()
        
        if self.generation_thread and self.generation_thread.is_alive():
            self.log_message("Generation cancellation requested.")
            self.update_status("Cancelling generation...")
            self.cancel_generation.set()

    def _thread_safe_display_results(self, content):
        self.root.after(0, self.display_results, content)

    def display_results(self, content):
        self.log_message("Generation complete. Opening output window.")
        show_output_window(self.root, content, self.log_message)

    def _thread_safe_reset_after_generation(self):
        self.root.after(0, self._reset_ui_after_generation)

    def _reset_ui_after_generation(self):
        self.ui.generate_button.config(state='normal')
        self.ui.browse_button.config(state='normal')
        self.ui.cancel_button.config(state='disabled')
        self.ui.progress_bar['value'] = 0
        
        duration_message = ""
        if self.operation_start_time:
            duration = time.time() - self.operation_start_time
            duration_message = f" Finished in {duration:.2f} seconds."
            self.operation_start_time = None

        status_message = "Generation cancelled." if self.cancel_generation.is_set() else "Generation complete."
        self.update_status(status_message + duration_message)

    def update_progress(self, current, total):
        """Thread-safe progress update."""
        def _update():
            self.ui.progress_bar['maximum'] = total
            self.ui.progress_bar['value'] = current
        self.root.after(0, _update)
        
    def update_status(self, message):
        """Thread-safe method to update the status label."""
        self.root.after(0, lambda: self.ui.status_label.config(text=message))

    def log_message(self, message):
        if self.verbose:
            print(message)

    def show_about(self):
        messagebox.showinfo(
            "About CodebaseToText",
            "Version: 7.3\n\n"
            "This application helps you package a codebase into a single markdown file for use with Large Language Models."
        )

    def show_settings(self):
        """Shows the settings window and re-scans if changes were saved."""
        settings_saved = show_settings_window(self.root, self.config)
        if settings_saved:
            self.ignored_items = self.config.get_ignored_set()
            
            current_folder = self.root_dir.get()
            if current_folder and os.path.isdir(current_folder):
                self.log_message("Settings updated. Automatically re-scanning directory...")
                self.update_status("Settings updated. Re-scanning directory...")
                self._load_folder(current_folder)
            else:
                self.log_message("Settings updated. No folder loaded to re-scan.")
                self.update_status("Settings updated. Select a folder to see changes.")


    def check_selected(self): self.tree_manager.check_selected()
    def uncheck_selected(self): self.tree_manager.uncheck_selected()
    def check_all(self): self.tree_manager.check_all()
    def uncheck_all(self): self.tree_manager.uncheck_all()

    def on_closing(self):
        self.config.config.read(self.config.config_file)
        self.config.set_setting('Settings', 'width', self.root.winfo_width())
        self.config.set_setting('Settings', 'height', self.root.winfo_height())
        self.config.set_setting('Settings', 'last_folder', self.root_dir.get())
        self.config.save_config()
        self.root.destroy()