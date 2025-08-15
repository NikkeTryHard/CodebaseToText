# main_app.py
from tkinterdnd2 import DND_FILES
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import threading
import os
from treeview_manager import TreeViewManager
from file_processor import generate_text_content, get_all_files
from output_window import show_output_window
from config_manager import ConfigManager
from ui import UI

class DirectoryToTextApp:
    """
    Main application class for the Directory to Text GUI.
    Handles application state, logic, and coordination between modules.
    """
    def __init__(self, root, verbose=False):
        self.root = root
        self.verbose = verbose
        self.config = ConfigManager()
        
        self._setup_window()
        
        # --- Application State Variables ---
        self.root_dir = tk.StringVar(value=self.config.get_setting('Settings', 'last_folder', ''))
        self.include_all_var = tk.BooleanVar(value=False)
        
        # --- UI and Manager Initialization ---
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
        
        # Configure a special style for ignored items in the treeview
        self.ui.tree.tag_configure('ignored', foreground='gray')
        
        self.ignored_items = self.config.get_ignored_set()
        self.tree_manager = TreeViewManager(self.ui.tree, self.root, self.log_message, self.ignored_items)
        
        self._setup_event_bindings()
        
        # --- Initial Load ---
        if self.root_dir.get():
            self._load_folder(self.root_dir.get())

    def _setup_window(self):
        """Configures the main application window."""
        width = self.config.get_setting('Settings', 'width', '800')
        height = self.config.get_setting('Settings', 'height', '700')
        self.root.title("Folder to LLM-Ready Text v6.4")
        self.root.geometry(f"{width}x{height}")
        
        theme = self.config.get_setting('Settings', 'theme', 'dark')
        if theme not in ['dark', 'light']:
            theme = 'dark' # Default to dark if config is invalid
            
        self.root.tk.call('source', 'azure.tcl')
        self.root.tk.call('set_theme', theme)

    def _setup_event_bindings(self):
        """Sets up drag-and-drop and window closing protocols."""
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.handle_drop)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _load_folder(self, folder_path):
        """Loads a folder's contents, updating the UI and treeview."""
        if not os.path.isdir(folder_path):
            self.log_message(f"Attempted to load invalid path: {folder_path}")
            messagebox.showerror("Error", f"The selected path '{folder_path}' is not a valid directory.")
            return
            
        self.root_dir.set(folder_path)
        self.log_message(f"Selected folder: {folder_path}")
        
        self.include_all_var.set(False)
        self.on_toggle_include_all()
        self.ui.include_all_toggle.config(state='normal')
        
        self.tree_manager.populate_treeview(folder_path)
        self.ui.run_button.config(state='normal')

    def select_folder(self):
        """Opens a dialog to select a folder."""
        last_folder = self.config.get_setting('Settings', 'last_folder', '')
        folder_selected = filedialog.askdirectory(initialdir=last_folder if os.path.isdir(last_folder) else None)
        if folder_selected:
            self._load_folder(folder_selected)

    def handle_drop(self, event):
        """Handles a drag-and-drop event."""
        if event.data:
            folder_path = event.data.strip()
            self._load_folder(folder_path)

    def on_toggle_include_all(self):
        """Handles the toggling of the 'include all' checkbox."""
        if self.include_all_var.get():
            self.log_message("Annotated Tree Mode: Tree will show all files. Unchecked files will be marked as omitted.")
        else:
            self.log_message("Standard Mode: Tree shows all folders, checked files, and a summary of omitted files.")

    def start_conversion_thread(self):
        """Validates inputs and starts the background thread for text generation."""
        root_path = self.root_dir.get()
        if not root_path or not os.path.isdir(root_path):
            messagebox.showerror("Error", "Please select a valid root directory first.")
            return

        files_for_content = self.tree_manager.get_checked_files()
        files_for_tree = get_all_files(root_path)
        is_annotated_mode = self.include_all_var.get()

        if not files_for_tree:
            messagebox.showwarning("No Files Found", "No files were found in the directory.")
            return
        if not files_for_content:
            messagebox.showwarning("No Files Selected", "Please check at least one file to include its content in the output.")
            return
        
        self.log_message("Starting generation...")
        self.ui.run_button.config(state='disabled', text="Processing...")
        self.ui.progress_bar['maximum'] = len(files_for_content)
        self.ui.progress_bar['value'] = 0

        thread = threading.Thread(
            target=generate_text_content,
            args=(root_path, files_for_tree, files_for_content, is_annotated_mode, self.ignored_items, self.log_message, self.display_results, self.enable_run_button, self.update_progress),
            daemon=True
        )
        thread.start()

    def display_results(self, content):
        """Displays the generated content in a new window."""
        self.log_message("Generation complete. Opening output window.")
        show_output_window(self.root, content, self.log_message)

    def enable_run_button(self):
        """Callback to re-enable the 'Generate' button after processing."""
        self.ui.run_button.config(state='normal', text="Generate Text")
        self.ui.progress_bar['value'] = 0

    def update_progress(self):
        """Updates the progress bar by one step."""
        self.ui.progress_bar['value'] += 1

    def log_message(self, message):
        """Logs a message to the console if verbose mode is enabled."""
        if self.verbose:
            print(message)

    def show_about(self):
        """Displays the about message box."""
        messagebox.showinfo(
            "About Folder to LLM-Ready Text",
            "Version: 6.4\n\n"
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
        """Saves configuration on window close."""
        self.config.set_setting('Settings', 'width', self.root.winfo_width())
        self.config.set_setting('Settings', 'height', self.root.winfo_height())
        self.config.set_setting('Settings', 'last_folder', self.root_dir.get())
        self.config.save_config()
        self.root.destroy()