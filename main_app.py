# main_app.py
import sys
import os
import time
import threading
import traceback
from tkinterdnd2 import DND_FILES
import tkinter as tk
from tkinter import filedialog, messagebox
from treeview_manager import TreeViewManager
from output_window import show_output_window
from config_manager import ConfigManager
from ui import UI
from scanner import scan_directory_fast
from generator import generate_text_content_fast
from settings_window import show_settings_window

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class DirectoryToTextApp:
    """Enhanced main application class with better error handling and UI integration."""
    
    def __init__(self, root, verbose=False, config_file=None):
        self.root = root
        self.verbose = verbose
        
        # Initialize config manager with optional custom config file
        if config_file:
            self.config = ConfigManager(config_file)
        else:
            self.config = ConfigManager()
            
        self.root_dir = tk.StringVar(value=self.config.get_setting('Settings', 'last_folder'))
        
        # Initialize state variables
        self.scanned_tree_data = None
        self.scan_thread = None
        self.generation_thread = None
        self.cancel_scan = threading.Event()
        self.cancel_generation = threading.Event()
        self.operation_start_time = None
        self.current_operation = None
        
        # Setup UI and components
        self._setup_window()
        self._setup_ui()
        self._setup_event_bindings()
        
        # Load last folder if available
        if self.root_dir.get() and os.path.isdir(self.root_dir.get()):
            self.root.after(100, lambda: self._load_folder(self.root_dir.get()))

    def _setup_window(self):
        """Setup the main window with enhanced configuration."""
        try:
            width = self.config.get_setting('Settings', 'width')
            height = self.config.get_setting('Settings', 'height')
            self.root.title("CodebaseToText v7.4 - Enhanced Edition")
            self.root.geometry(f"{width}x{height}")
            
            # Apply theme
            theme = self.config.get_setting('Settings', 'theme')
            if theme not in ['dark', 'light']:
                theme = 'dark'
                
            azure_path = resource_path('azure.tcl')
            self.root.tk.call('source', azure_path)
            self.root.tk.call('set_theme', theme)
            
            # Set window icon if available
            try:
                icon_path = resource_path('assets/icon.ico')
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
            except:
                pass  # Icon not critical
                
        except Exception as e:
            self._log_error(f"Error setting up window: {e}")

    def _setup_ui(self):
        """Setup the enhanced UI with callbacks."""
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
            'refresh_tree': self._refresh_tree,
            'sort_tree': self.sort_tree,
        }
        
        self.ui = UI(self.root, callbacks, self.root_dir)
        
        # Configure tree styling
        self.ui.tree.tag_configure('ignored', foreground='gray')
        self.ui.tree.tag_configure('highlight', background='#0078d4', foreground='white')
        
        # Setup tree manager
        self.ignored_items = self.config.get_ignored_set()
        self.tree_manager = TreeViewManager(
            self.ui.tree, self.root, self.log_message,
            self.ignored_items, resource_path,
            ignore_callback=self.add_to_ignore_list
        )
        self.root.global_app_instance = self # For context menu access

    def _setup_event_bindings(self):
        """Setup event bindings with error handling."""
        try:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.handle_drop)
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            # Add keyboard shortcuts
            self.root.bind('<Control-o>', lambda e: self.select_folder())
            self.root.bind('<Control-s>', lambda e: self.show_settings())
            self.root.bind('<Control-q>', lambda e: self.on_closing())
            self.root.bind('<F5>', lambda e: self._refresh_tree())
            
        except Exception as e:
            self._log_error(f"Error setting up event bindings: {e}")

    def _load_folder(self, folder_path):
        """Load and scan a folder with enhanced error handling."""
        try:
            if not os.path.isdir(folder_path):
                self._show_error(f"The selected path '{folder_path}' is not a valid directory.")
                return
                
            self.root_dir.set(folder_path)
            self._update_status("Scanning folder...", "blue")
            self.log_message(f"Scanning folder: {folder_path}")
            
            # Clear previous data and setup UI
            self.scanned_tree_data = None
            self.tree_manager.clear_tree()
            self.ui.tree.insert("", "end", text="  🔍 Scanning and analyzing files, please wait...")
            
            # Disable UI during scan
            self._set_ui_state(scanning=True)
            self.operation_start_time = time.time()
            self.current_operation = "scan"
            
            # Start scan thread
            self.cancel_scan.clear()
            self.scan_thread = threading.Thread(
                target=self._scan_folder_thread_fast,
                args=(folder_path, self.cancel_scan),
                daemon=True
            )
            self.scan_thread.start()
            
        except Exception as e:
            self._log_error(f"Error loading folder: {e}")
            self._show_error(f"Failed to load folder: {e}")

    def _scan_folder_thread_fast(self, folder_path, cancel_event):
        """Worker function to scan directory with enhanced error handling."""
        tree_data = None
        try:
            tree_data = scan_directory_fast(folder_path, self.ignored_items, cancel_event)
            if tree_data and not cancel_event.is_set():
                self.scanned_tree_data = tree_data
                self.root.after(0, self._populate_tree_ui, tree_data)
            elif cancel_event.is_set():
                self.root.after(0, self._reset_ui_after_scan, True)
                
        except Exception as e:
            error_msg = f"Error scanning directory: {e}"
            self.log_message(error_msg)
            self.log_message(traceback.format_exc())
            self.root.after(0, lambda: self._show_error(error_msg))
        finally:
            self.log_message("Scan thread finished.")
            self.root.after(0, self._reset_ui_after_scan, cancel_event.is_set())

    def _populate_tree_ui(self, tree_data):
        """Callback to update the treeview on the main thread."""
        try:
            self.log_message("Populating tree UI...")
            self._update_status("Scan complete. Populating UI...", "blue")
            self.log_message("Scan complete. Populating UI.")
            self.tree_manager.populate_from_data(tree_data)
            
            # Show success message
            self._update_status("Scan complete! Select files and generate output.", "green")
            self.ui.show_success_animation()
            
        except Exception as e:
            self._log_error(f"Error populating tree UI: {e}")
            self._show_error(f"Failed to populate tree view: {e}")

    def _reset_ui_after_scan(self, cancelled=False):
        """Resets the UI state after a scan finishes or is cancelled."""
        try:
            self.log_message(f"Resetting UI after scan. Cancelled: {cancelled}")
            self._set_ui_state(scanning=False)
            self.current_operation = None
            
            duration_message = ""
            if self.operation_start_time:
                duration = time.time() - self.operation_start_time
                duration_message = f" Finished in {duration:.2f} seconds."
                self.operation_start_time = None

            if cancelled:
                self.tree_manager.clear_tree()
                self.ui.tree.insert("", "end", text="  ❌ Scan cancelled by user.")
                self.log_message("Scan was cancelled.")
                self._update_status("Scan cancelled." + duration_message, "orange")
            else:
                self._update_status("Scan complete." + duration_message, "green")
                
        except Exception as e:
            self._log_error(f"Error resetting UI after scan: {e}")

    def select_folder(self):
        """Select a folder with enhanced error handling."""
        try:
            last_folder = self.config.get_setting('Settings', 'last_folder')
            initial_dir = last_folder if os.path.isdir(last_folder) else None
            
            folder_selected = filedialog.askdirectory(
                initialdir=initial_dir,
                title="Select Root Folder for Codebase"
            )
            
            if folder_selected:
                self._load_folder(folder_selected)
                
        except Exception as e:
            self._log_error(f"Error selecting folder: {e}")
            self._show_error(f"Failed to select folder: {e}")

    def handle_drop(self, event):
        """Handle drag and drop with validation."""
        try:
            if event.data:
                folder_path = event.data.strip()
                # Remove quotes if present
                folder_path = folder_path.strip('"{}')
                
                if os.path.isdir(folder_path):
                    self._load_folder(folder_path)
                else:
                    self._show_error("Please drop a folder, not a file.")
                    
        except Exception as e:
            self._log_error(f"Error handling drop: {e}")
            self._show_error(f"Failed to process dropped item: {e}")

    def start_conversion_thread(self):
        """Start text generation with enhanced validation."""
        try:
            root_path = self.root_dir.get()
            if not self.scanned_tree_data:
                self._show_error("No directory has been scanned successfully. Please scan a folder first.")
                return

            files_for_content = self.tree_manager.get_checked_files()
            if not files_for_content:
                self._show_error("No files are selected. Please check some files before generating.")
                return
            
            self.log_message("Starting generation...")
            self._set_ui_state(generating=True)
            self._update_status("Starting generation...", "blue")
            self.operation_start_time = time.time()
            self.current_operation = "generate"
            
            # Reset progress
            self.ui.progress_bar['value'] = 0
            self.cancel_generation.clear()

            # Start generation thread
            self.generation_thread = threading.Thread(
                target=generate_text_content_fast,
                args=(
                    root_path, self.scanned_tree_data, files_for_content, 
                    self.log_message, self._thread_safe_display_results, 
                    self._thread_safe_reset_after_generation,
                    self.cancel_generation, self._update_status, self._update_progress
                ),
                daemon=True
            )
            self.generation_thread.start()
            
        except Exception as e:
            self._log_error(f"Error starting conversion: {e}")
            self._show_error(f"Failed to start conversion: {e}")

    def cancel_current_operation(self):
        """Cancel current operation with user confirmation."""
        try:
            if self.current_operation == "scan" and self.scan_thread and self.scan_thread.is_alive():
                if messagebox.askyesno("Cancel Scan", "Are you sure you want to cancel the scan?"):
                    self.log_message("Scan cancellation requested.")
                    self._update_status("Cancelling scan...", "orange")
                    self.cancel_scan.set()
                    
            elif self.current_operation == "generate" and self.generation_thread and self.generation_thread.is_alive():
                if messagebox.askyesno("Cancel Generation", "Are you sure you want to cancel the generation?"):
                    self.log_message("Generation cancellation requested.")
                    self._update_status("Cancelling generation...", "orange")
                    self.cancel_generation.set()
            else:
                self._show_info("No operation in progress to cancel.")
                
        except Exception as e:
            self._log_error(f"Error cancelling operation: {e}")

    def _thread_safe_display_results(self, content):
        """Thread-safe method to display results."""
        self.root.after(0, self.display_results, content)

    def display_results(self, content):
        """Display generation results with error handling."""
        try:
            self.log_message("Generation complete. Opening output window.")
            self._update_status("Generation complete! Opening output window...", "green")
            
            window = show_output_window(self.root, content, self.log_message, self.config)
            if not window:
                self._show_error("Failed to create output window.")
                
        except Exception as e:
            self._log_error(f"Error displaying results: {e}")
            self._show_error(f"Failed to display results: {e}")

    def _thread_safe_reset_after_generation(self):
        """Thread-safe method to reset UI after generation."""
        self.root.after(0, self._reset_ui_after_generation)

    def _reset_ui_after_generation(self):
        """Reset UI state after generation completes."""
        try:
            self._set_ui_state(generating=False)
            self.current_operation = None
            
            duration_message = ""
            if self.operation_start_time:
                duration = time.time() - self.operation_start_time
                duration_message = f" Finished in {duration:.2f} seconds."
                self.operation_start_time = None

            if self.cancel_generation.is_set():
                status_message = "Generation cancelled."
                color = "orange"
            else:
                status_message = "Generation complete."
                color = "green"
                
            self._update_status(status_message + duration_message, color)
            
        except Exception as e:
            self._log_error(f"Error resetting UI after generation: {e}")

    def _update_progress(self, current, total):
        """Update progress with enhanced feedback."""
        try:
            self.ui.update_progress(current, total)
        except Exception as e:
            self._log_error(f"Error updating progress: {e}")

    def _update_status(self, message, color="black"):
        """Update status with color coding."""
        try:
            self.ui.update_status(message)
            # Color coding is handled in the UI class
        except Exception as e:
            self._log_error(f"Error updating status: {e}")

    def _set_ui_state(self, scanning=False, generating=False):
        """Set UI state based on current operation."""
        try:
            if scanning or generating:
                self.ui.show_loading_state(True)
                self.ui.cancel_button.config(state='normal')
            else:
                self.ui.show_loading_state(False)
                self.ui.cancel_button.config(state='disabled')
                
        except Exception as e:
            self._log_error(f"Error setting UI state: {e}")

    def _refresh_tree(self):
        """Refresh the tree view by re-scanning the current folder."""
        try:
            current_folder = self.root_dir.get()
            if current_folder and os.path.isdir(current_folder):
                self.log_message("Refreshing tree view...")
                self._load_folder(current_folder)
            else:
                self._show_info("No folder loaded to refresh.")
                
        except Exception as e:
            self._log_error(f"Error refreshing tree: {e}")

    def _show_error(self, message):
        """Show error message with proper formatting."""
        try:
            messagebox.showerror("Error", message)
        except Exception as e:
            self.log_message(f"Error showing error dialog: {e}")

    def _show_info(self, message):
        """Show info message."""
        try:
            messagebox.showinfo("Information", message)
        except Exception as e:
            self.log_message(f"Error showing info dialog: {e}")

    def _log_error(self, message):
        """Log error with traceback for debugging."""
        if self.verbose:
            print(f"ERROR: {message}")
            traceback.print_exc()
        self.log_message(f"Error: {message}")

    def log_message(self, message):
        """Log message with timestamp if verbose mode is enabled."""
        if self.verbose:
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] {message}")

    def show_about(self):
        """Show enhanced about dialog."""
        try:
            about_text = """CodebaseToText v7.4 - Enhanced Edition

🎯 Convert your codebase to LLM-ready markdown
✨ Enhanced UI with animations and better UX
🛡️ Improved error handling and robustness
⚡ Faster processing and better performance

Features:
• Drag & drop folder support
• Smart file filtering and ignoring
• Progress tracking and status updates
• Multiple output formats
• Theme support (Dark/Light)
• Keyboard shortcuts

Built with Python and Tkinter
Enhanced for better user experience"""
            
            messagebox.showinfo("About CodebaseToText", about_text)
            
        except Exception as e:
            self._log_error(f"Error showing about dialog: {e}")

    def show_settings(self):
        """Show settings window with enhanced error handling."""
        try:
            settings_saved = show_settings_window(self.root, self.config)
            if settings_saved:
                self.ignored_items = self.config.get_ignored_set()
                
                current_folder = self.root_dir.get()
                if current_folder and os.path.isdir(current_folder):
                    self.log_message("Settings updated. Automatically re-scanning directory...")
                    self._update_status("Settings updated. Re-scanning directory...", "blue")
                    self._load_folder(current_folder)
                else:
                    self.log_message("Settings updated. No folder loaded to re-scan.")
                    self._update_status("Settings updated. Select a folder to see changes.", "green")
                    
        except Exception as e:
            self._log_error(f"Error showing settings: {e}")
            self._show_error(f"Failed to open settings: {e}")

    # Tree manager delegate methods
    def check_selected(self): 
        try:
            self.tree_manager.check_selected()
        except Exception as e:
            self._log_error(f"Error checking selected: {e}")
            
    def uncheck_selected(self): 
        try:
            self.tree_manager.uncheck_selected()
        except Exception as e:
            self._log_error(f"Error unchecking selected: {e}")
            
    def check_all(self): 
        try:
            self.tree_manager.check_all()
        except Exception as e:
            self._log_error(f"Error checking all: {e}")
            
    def uncheck_all(self):
        try:
            self.tree_manager.uncheck_all()
        except Exception as e:
            self._log_error(f"Error unchecking all: {e}")

    def sort_tree(self, sort_key):
        """Sort the tree view based on the selected key."""
        try:
            self.log_message(f"Sorting tree by: {sort_key}")
            self.tree_manager.sort_tree_data(sort_key)
        except Exception as e:
            self._log_error(f"Error sorting tree: {e}")

    def add_to_ignore_list(self, item_path):
        """Add an item to the ignore list and re-scan."""
        try:
            # Normalize the path for consistency
            normalized_path = item_path.replace(os.path.sep, '/')
            
            # Get current ignore list
            current_ignore_list = self.config.get_setting('Settings', 'ignore_list')
            ignore_lines = current_ignore_list.split('\n')
            
            # Add the new item if it's not already there
            if normalized_path not in ignore_lines:
                new_ignore_list = current_ignore_list + '\n' + normalized_path
                self.config.set_setting('Settings', 'ignore_list', new_ignore_list.strip())
                self.config.save_config()
                
                # Update in-memory ignore list for the current session
                self.ignored_items = self.config.get_ignored_set()
                self.tree_manager.ignored_items = self.ignored_items
                
                self.log_message(f"Added '{normalized_path}' to ignore list. Refreshing...")
                self._refresh_tree()
            else:
                self.log_message(f"'{normalized_path}' is already in the ignore list.")

        except Exception as e:
            self._log_error(f"Error adding to ignore list: {e}")

    def on_closing(self):
        """Handle application closing with enhanced cleanup."""
        try:
            # Cancel any ongoing operations
            if self.current_operation:
                if messagebox.askyesno("Confirm Exit",
                                     f"A {self.current_operation} operation is in progress. "
                                     "Are you sure you want to exit?"):
                    self.cancel_scan.set()
                    self.cancel_generation.set()
                else:
                    return
            
            # Save configuration
            self.config.config.read(self.config.config_file)
            self.config.set_setting('Settings', 'width', self.root.winfo_width())
            self.config.set_setting('Settings', 'height', self.root.winfo_height())
            last_folder_to_save = self.root_dir.get()
            self.log_message(f"Saving last_folder: {last_folder_to_save}")
            self.config.set_setting('Settings', 'last_folder', last_folder_to_save)
            self.config.save_config()
            
            self.log_message("Application closing. Configuration saved.")
            self.root.destroy()
            
        except Exception as e:
            self._log_error(f"Error during application closing: {e}")
            self.root.destroy()