# main_app.py
import sys
import os
from tkinterdnd2 import DND_FILES
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
from treeview_manager import TreeViewManager
from file_processor import generate_text_content, get_all_files, scan_directory
from output_window import show_output_window
from config_manager import ConfigManager
from ui import UI

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
        self._setup_window()
        self.root_dir = tk.StringVar(value=self.config.get_setting('Settings', 'last_folder', ''))
        self.include_all_var = tk.BooleanVar(value=False)
        callbacks = {
            'select_folder': self.select_folder,
            'check_selected': self.check_selected,
            'uncheck_selected': self.uncheck_selected,
            'check_all': self.check_all,
            'uncheck_all': self.uncheck_all,
            'toggle_include_all': self.on_toggle_include_all,
            'start_conversion': self.start_conversion_thread,
            'exit': self.on_closing,
            'show_about': self.show_about,
        }
        self.ui = UI(self.root, callbacks, self.root_dir, self.include_all_var)
        self.ui.tree.tag_configure('ignored', foreground='gray')
        self.ignored_items = self.config.get_ignored_set()
        self.tree_manager = TreeViewManager(self.ui.tree, self.root, self.log_message, self.ignored_items)
        self._setup_event_bindings()
        if self.root_dir.get():
            self._load_folder(self.root_dir.get())

    def _setup_window(self):
        width = self.config.get_setting('Settings', 'width', '800')
        height = self.config.get_setting('Settings', 'height', '700')
        self.root.title("CodebaseToText v6.7") 
        self.root.geometry(f"{width}x{height}")
        theme = self.config.get_setting('Settings', 'theme', 'dark')
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
        
        self.tree_manager.clear_tree()
        self.ui.tree.insert("", "end", text="  Scanning directory, please wait...")
        self.ui.run_button.config(state='disabled')
        self.ui.browse_button.config(state='disabled')
        
        thread = threading.Thread(
            target=self._scan_folder_thread,
            args=(folder_path,),
            daemon=True
        )
        thread.start()

    def _scan_folder_thread(self, folder_path):
        """Worker function to scan directory in the background."""
        try:
            tree_data = scan_directory(folder_path, self.ignored_items)
            self.root.after(0, self._populate_tree_ui, tree_data)
        except Exception as e:
            self.log_message(f"Error scanning directory: {e}")
            self.root.after(0, self._scan_failed)

    def _populate_tree_ui(self, tree_data):
        """Callback to update the treeview on the main thread."""
        self.log_message("Scan complete. Populating UI.")
        self.tree_manager.populate_from_data(tree_data)
        
        self.include_all_var.set(False)
        self.on_toggle_include_all()
        self.ui.include_all_toggle.config(state='normal')
        self.ui.run_button.config(state='normal')
        self.ui.browse_button.config(state='normal')

    def _scan_failed(self):
        """Callback if scanning fails."""
        self.tree_manager.clear_tree()
        self.ui.tree.insert("", "end", text="  Failed to scan directory.")
        self.ui.browse_button.config(state='normal')

    def select_folder(self):
        last_folder = self.config.get_setting('Settings', 'last_folder', '')
        folder_selected = filedialog.askdirectory(initialdir=last_folder if os.path.isdir(last_folder) else None)
        if folder_selected:
            self._load_folder(folder_selected)

    def handle_drop(self, event):
        if event.data:
            folder_path = event.data.strip()
            self._load_folder(folder_path)

    def on_toggle_include_all(self):
        if self.include_all_var.get():
            self.log_message("Annotated Tree Mode: Tree will show all files. Unchecked items will be marked as omitted.")
        else:
            self.log_message("Standard Mode: Tree shows only selected items. Unselected folders will be collapsed.")

    def start_conversion_thread(self):
        root_path = self.root_dir.get()
        if not root_path or not os.path.isdir(root_path):
            messagebox.showerror("Error", "Please select a valid root directory first.")
            return

        files_for_content = self.tree_manager.get_checked_files()
        item_states = self.tree_manager.get_all_item_states()
        is_annotated_mode = self.include_all_var.get()
        
        if not files_for_content and not is_annotated_mode:
            messagebox.showwarning("No Files Selected", "Please check at least one file to include its content in the output.")
            return
        
        files_for_tree = get_all_files(root_path)
        if not files_for_tree:
            messagebox.showwarning("No Files Found", "No files were found in the directory.")
            return
        
        self.log_message("Starting generation...")
        self.ui.run_button.config(state='disabled', text="Processing...")
        self.update_status("Starting...")
        self.ui.progress_bar['maximum'] = len(files_for_content)
        self.ui.progress_bar['value'] = 0

        thread = threading.Thread(
            target=generate_text_content,
            args=(root_path, files_for_tree, files_for_content, is_annotated_mode, self.ignored_items, item_states, self.log_message, self.display_results, self.enable_run_button, self.update_progress, self.update_status),
            daemon=True
        )
        thread.start()

    def display_results(self, content):
        self.log_message("Generation complete. Opening output window.")
        show_output_window(self.root, content, self.log_message)

    def enable_run_button(self):
        self.ui.run_button.config(state='normal', text="Generate Text")
        self.ui.progress_bar['value'] = 0
        self.root.after(2000, lambda: self.update_status(""))

    def update_progress(self):
        self.ui.progress_bar['value'] += 1
        
    def update_status(self, message):
        """Thread-safe method to update the status label."""
        self.root.after(0, lambda: self.ui.status_label.config(text=message))

    def log_message(self, message):
        if self.verbose:
            print(message)

    def show_about(self):
        messagebox.showinfo(
            "About CodebaseToText",
            "Version: 6.7\n\n"
            "This application helps you package a codebase into a single markdown file for use with Large Language Models."
        )

    def check_selected(self):
        self.tree_manager.check_selected()

    def uncheck_selected(self):
        self.tree_manager.uncheck_selected()

    def check_all(self):
        self.tree_manager.check_all()

    def uncheck_all(self):
        self.tree_manager.uncheck_all()

    def on_closing(self):
        self.config.set_setting('Settings', 'width', self.root.winfo_width())
        self.config.set_setting('Settings', 'height', self.root.winfo_height())
        self.config.set_setting('Settings', 'last_folder', self.root_dir.get())
        self.config.save_config()
        self.root.destroy()