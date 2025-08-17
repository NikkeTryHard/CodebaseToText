# settings_window.py
import tkinter as tk
from tkinter import ttk, scrolledtext

class SettingsWindow(tk.Toplevel):
    """
    A modal dialog window for editing application preferences,
    such as the ignore list.
    """
    def __init__(self, parent, config_manager):
        super().__init__(parent)
        self.parent = parent
        self.config = config_manager
        self.saved = False

        self.title("Preferences")
        self.transient(parent)
        self.grab_set()
        
        # Center the window relative to the parent
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        win_width = 400
        win_height = 300
        x = parent_x + (parent_width // 2) - (win_width // 2)
        y = parent_y + (parent_height // 2) - (win_height // 2)
        self.geometry(f"{win_width}x{win_height}+{x}+{y}")
        self.minsize(300, 250)

        self.create_widgets()
        self.load_settings()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        ttk.Label(main_frame, text="Ignore List (one item per line):").grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.text_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=10)
        self.text_area.grid(row=1, column=0, sticky="nsew")

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, sticky="e", pady=(10, 0))

        save_button = ttk.Button(button_frame, text="Save", command=self.save_settings, style="Accent.TButton")
        save_button.pack(side=tk.LEFT, padx=5)

        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.destroy)
        cancel_button.pack(side=tk.LEFT)

    def load_settings(self):
        """Loads settings from the config manager into the UI."""
        ignore_list_str = self.config.get_setting('Settings', 'ignore_list')
        # Convert comma-separated string to a newline-separated string for display
        items = [item.strip() for item in ignore_list_str.split(',') if item.strip()]
        self.text_area.insert('1.0', '\n'.join(items))

    def save_settings(self):
        """Saves settings from the UI back to the config manager."""
        text_content = self.text_area.get('1.0', tk.END).strip()
        # Convert newline-separated string back to a comma-separated string for storage
        items = [item.strip() for item in text_content.split('\n') if item.strip()]
        comma_separated_list = ','.join(items)

        self.config.set_setting('Settings', 'ignore_list', comma_separated_list)
        self.config.save_config()
        self.saved = True
        self.destroy()

def show_settings_window(parent, config_manager):
    """Creates, displays, and waits for the settings window to close."""
    dialog = SettingsWindow(parent, config_manager)
    parent.wait_window(dialog)
    return dialog.saved