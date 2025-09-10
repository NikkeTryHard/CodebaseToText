# settings_window.py
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os

class EnhancedSettingsWindow(tk.Toplevel):
    """
    An enhanced modal dialog window for editing application preferences,
    such as the ignore list, with better UI and functionality.
    """
    def __init__(self, parent, config_manager):
        super().__init__(parent)
        self.parent = parent
        self.config = config_manager
        self.saved = False
        self.animation_running = False

        self.title("Preferences")
        self.transient(parent)
        self.grab_set()
        
        # Center the window relative to the parent
        self._center_window()
        self.minsize(600, 500)

        self._create_ui()
        self._setup_animations()
        self.load_settings()

    def _center_window(self):
        """Center the window relative to the parent."""
        try:
            parent_x = self.parent.winfo_x()
            parent_y = self.parent.winfo_y()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()
            win_width = 500
            win_height = 400
            x = parent_x + (parent_width // 2) - (win_width // 2)
            y = parent_y + (parent_height // 2) - (win_height // 2)
            self.geometry(f"{win_width}x{win_height}+{x}+{y}")
        except:
            # Fallback centering
            self.geometry("500x400")

    def _create_ui(self):
        """Create the enhanced UI."""
        # Configure styles
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Segoe UI', 12, 'bold'))
        style.configure('Section.TLabel', font=('Segoe UI', 10, 'bold'))
        style.configure('Action.TButton', font=('Segoe UI', 10, 'bold'))
        
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        title_label = ttk.Label(header_frame, text="⚙️ Preferences", style="Title.TLabel")
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = ttk.Label(header_frame, text="Configure application settings", 
                                 foreground="gray", font=('Segoe UI', 9))
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0))

        # Settings sections
        self._create_ignore_section(main_frame)
        self._create_theme_section(main_frame)
        self._create_advanced_section(main_frame)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, sticky="ew", pady=(15, 0))

        # Left side - additional actions
        left_buttons = ttk.Frame(button_frame)
        left_buttons.pack(side=tk.LEFT)
        
        self.reset_button = ttk.Button(left_buttons, text="🔄 Reset to Defaults", 
                                      command=self._reset_to_defaults, style="Action.TButton")
        self.reset_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.help_button = ttk.Button(left_buttons, text="❓ Help", 
                                     command=self._show_help, style="Action.TButton")
        self.help_button.pack(side=tk.LEFT)

        # Right side - main actions
        right_buttons = ttk.Frame(button_frame)
        right_buttons.pack(side=tk.RIGHT)

        self.save_button = ttk.Button(right_buttons, text="💾 Save", 
                                     command=self.save_settings, style="Accent.TButton")
        self.save_button.pack(side=tk.RIGHT, padx=(10, 0))

        self.cancel_button = ttk.Button(right_buttons, text="❌ Cancel", 
                                       command=self.destroy)
        self.cancel_button.pack(side=tk.RIGHT)

    def _create_ignore_section(self, parent):
        """Create the ignore list section."""
        ignore_frame = ttk.LabelFrame(parent, text="📁 Ignore List", padding="10")
        ignore_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        ignore_frame.grid_rowconfigure(0, weight=1)
        ignore_frame.grid_columnconfigure(0, weight=1)
        
        # Description
        description = ttk.Label(ignore_frame, 
                              text="Files and folders to ignore during scanning (one item per line):",
                              font=('Segoe UI', 9))
        description.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        # Text area with better styling
        text_frame = ttk.Frame(ignore_frame)
        text_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)
        
        self.text_area = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            height=12,
            font=('Consolas', 10),
            padx=10,
            pady=10,
            selectbackground="#0078d4",
            selectforeground="white"
        )
        self.text_area.grid(row=0, column=0, sticky="nsew")
        
        # Quick actions frame
        quick_actions = ttk.Frame(ignore_frame)
        quick_actions.grid(row=2, column=0, sticky="ew")
        
        ttk.Button(quick_actions, text="📋 Common Patterns", 
                  command=self._add_common_patterns).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(quick_actions, text="🧹 Clear All", 
                  command=self._clear_ignore_list).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(quick_actions, text="📝 Validate", 
                  command=self._validate_ignore_list).pack(side=tk.LEFT)

    def _create_theme_section(self, parent):
        """Create the theme selection section."""
        theme_frame = ttk.LabelFrame(parent, text="🎨 Theme", padding="10")
        theme_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        
        # Theme selection
        theme_label = ttk.Label(theme_frame, text="Application theme:", font=('Segoe UI', 9))
        theme_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.theme_var = tk.StringVar(value=self.config.get_setting('Settings', 'theme'))
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var, 
                                  values=['dark', 'light'], state='readonly', width=10)
        theme_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Preview button
        preview_button = ttk.Button(theme_frame, text="👁️ Preview", 
                                   command=self._preview_theme, style="Action.TButton")
        preview_button.pack(side=tk.LEFT)
        
        # Theme info
        theme_info = ttk.Label(theme_frame, text="💡 Theme changes take effect after restart", 
                              foreground="gray", font=('Segoe UI', 8))
        theme_info.pack(side=tk.RIGHT)

    def _create_advanced_section(self, parent):
        """Create the advanced settings section."""
        advanced_frame = ttk.LabelFrame(parent, text="🔧 Advanced Settings", padding="10")
        advanced_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        
        # Grid layout for advanced options
        advanced_frame.grid_columnconfigure(1, weight=1)
        
        # Max file size
        ttk.Label(advanced_frame, text="Max file size (MB):", font=('Segoe UI', 9)).grid(row=0, column=0, sticky="w", pady=2)
        self.max_file_size_var = tk.StringVar(value="10")
        max_size_entry = ttk.Entry(advanced_frame, textvariable=self.max_file_size_var, width=10)
        max_size_entry.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=2)
        
        # Auto-save
        self.auto_save_var = tk.BooleanVar(value=True)
        auto_save_check = ttk.Checkbutton(advanced_frame, text="Auto-save settings", 
                                         variable=self.auto_save_var)
        auto_save_check.grid(row=1, column=0, columnspan=2, sticky="w", pady=2)
        
        # Verbose logging
        self.verbose_var = tk.BooleanVar(value=False)
        verbose_check = ttk.Checkbutton(advanced_frame, text="Verbose logging", 
                                       variable=self.verbose_var)
        verbose_check.grid(row=2, column=0, columnspan=2, sticky="w", pady=2)

    def _setup_animations(self):
        """Setup animation effects."""
        self.animation_running = False

    def _add_common_patterns(self):
        """Add common ignore patterns to the text area."""
        common_patterns = [
            "# Common build and cache directories",
            "node_modules/",
            ".git/",
            ".vscode/",
            "build/",
            "dist/",
            "target/",
            "bin/",
            "obj/",
            "",
            "# Common file types to ignore",
            "*.log",
            "*.tmp",
            "*.temp",
            "*.cache",
            "",
            "# OS generated files",
            ".DS_Store",
            "Thumbs.db",
            "desktop.ini"
        ]
        
        current_text = self.text_area.get('1.0', tk.END).strip()
        if current_text:
            current_text += "\n\n"
        
        new_text = current_text + "\n".join(common_patterns)
        self.text_area.delete('1.0', tk.END)
        self.text_area.insert('1.0', new_text)
        
        # Animate the button
        self._animate_button_success(self.reset_button, "📋 Added!")

    def _clear_ignore_list(self):
        """Clear the ignore list."""
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear the ignore list?"):
            self.text_area.delete('1.0', tk.END)
            self._animate_button_success(self.reset_button, "🧹 Cleared!")

    def _validate_ignore_list(self):
        """Validate the ignore list entries."""
        try:
            text_content = self.text_area.get('1.0', tk.END).strip()
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            
            valid_lines = []
            invalid_lines = []
            
            for line in lines:
                if line.startswith('#') or line.endswith('/') or '*' in line or '.' in line:
                    valid_lines.append(line)
                else:
                    invalid_lines.append(line)
            
            if invalid_lines:
                messagebox.showwarning("Validation Warning", 
                                     f"Some entries may not work as expected:\n\n" + 
                                     "\n".join(invalid_lines[:5]) + 
                                     ("\n..." if len(invalid_lines) > 5 else ""))
            else:
                messagebox.showinfo("Validation", "All entries look good! ✅")
                
        except Exception as e:
            messagebox.showerror("Validation Error", f"Error validating ignore list: {e}")

    def _preview_theme(self):
        """Preview the selected theme."""
        theme = self.theme_var.get()
        if theme in ['dark', 'light']:
            try:
                # Try to apply theme to current window for preview
                self.tk.call('set_theme', theme)
                messagebox.showinfo("Theme Preview", f"Previewing {theme} theme.\n\nNote: This is just a preview. The full theme will be applied after restart.")
            except:
                messagebox.showinfo("Theme Preview", f"Selected theme: {theme}\n\nTheme will be applied after restart.")
        else:
            messagebox.showerror("Invalid Theme", "Please select a valid theme.")

    def _reset_to_defaults(self):
        """Reset settings to default values."""
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset all settings to defaults?"):
            try:
                # Reset ignore list
                self.text_area.delete('1.0', tk.END)
                
                # Reset theme
                self.theme_var.set('dark')
                
                # Reset advanced settings
                self.max_file_size_var.set("10")
                self.auto_save_var.set(True)
                self.verbose_var.set(False)
                
                messagebox.showinfo("Reset Complete", "Settings have been reset to defaults.")
                
            except Exception as e:
                messagebox.showerror("Reset Error", f"Error resetting settings: {e}")

    def _show_help(self):
        """Show help information."""
        help_text = """
📁 Ignore List Help:

• Add file/folder names to ignore during scanning
• Use patterns like "*.log" to ignore all .log files
• Use "folder/" to ignore entire folders
• Lines starting with # are comments
• One item per line

🎨 Theme:
• Choose between dark and light themes
• Theme changes require restart

🔧 Advanced:
• Max file size: Files larger than this will be skipped
• Auto-save: Automatically save settings when changed
• Verbose logging: Show detailed operation logs

💡 Tips:
• Use the "Common Patterns" button to add typical ignores
• Validate your ignore list to catch potential issues
• Settings are automatically saved when you click Save
        """
        
        help_window = tk.Toplevel(self)
        help_window.title("Help")
        help_window.geometry("500x600")
        help_window.transient(self)
        help_window.grab_set()
        
        # Center help window
        x = self.winfo_x() + 50
        y = self.winfo_y() + 50
        help_window.geometry(f"+{x}+{y}")
        
        text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, padx=15, pady=15)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert('1.0', help_text)
        text_widget.config(state='disabled')
        
        close_button = ttk.Button(help_window, text="Close", command=help_window.destroy)
        close_button.pack(pady=10)

    def _animate_button_success(self, button, success_text):
        """Animate button with success text."""
        if self.animation_running:
            return
            
        self.animation_running = True
        original_text = button.cget('text')
        
        def animate():
            button.configure(text=success_text)
            self.after(1000, lambda: self._reset_button_text(button, original_text))
        
        animate()

    def _reset_button_text(self, button, text):
        """Reset button text after animation."""
        button.configure(text=text)
        self.animation_running = False

    def load_settings(self):
        """Load settings from the config manager into the UI."""
        try:
            # Load ignore list
            ignore_list_str = self.config.get_setting('Settings', 'ignore_list')
            items = [item.strip() for item in ignore_list_str.split(',') if item.strip()]
            self.text_area.insert('1.0', '\n'.join(items))
            
            # Load theme
            theme = self.config.get_setting('Settings', 'theme')
            if theme in ['dark', 'light']:
                self.theme_var.set(theme)
            
            # Load advanced settings
            max_size = self.config.get_setting('Settings', 'max_file_size', fallback='10')
            self.max_file_size_var.set(max_size)
            
            auto_save = self.config.get_setting('Settings', 'auto_save', fallback='True')
            self.auto_save_var.set(auto_save.lower() == 'true')
            
            verbose = self.config.get_setting('Settings', 'verbose', fallback='False')
            self.verbose_var.set(verbose.lower() == 'true')
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load settings: {e}")

    def save_settings(self):
        """Save settings from the UI back to the config manager."""
        try:
            # Save ignore list
            text_content = self.text_area.get('1.0', tk.END).strip()
            items = [item.strip() for item in text_content.split('\n') if item.strip()]
            comma_separated_list = ','.join(items)
            
            self.config.set_setting('Settings', 'ignore_list', comma_separated_list)
            
            # Save theme
            self.config.set_setting('Settings', 'theme', self.theme_var.get())
            
            # Save advanced settings
            self.config.set_setting('Settings', 'max_file_size', self.max_file_size_var.get())
            self.config.set_setting('Settings', 'auto_save', str(self.auto_save_var.get()))
            self.config.set_setting('Settings', 'verbose', str(self.verbose_var.get()))
            
            # Save to file
            self.config.save_config()
            
            self.saved = True
            
            # Show success message
            messagebox.showinfo("Success", "Settings saved successfully! ✅")
            
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

def show_settings_window(parent, config_manager):
    """Creates, displays, and waits for the enhanced settings window to close."""
    try:
        dialog = EnhancedSettingsWindow(parent, config_manager)
        parent.wait_window(dialog)
        return dialog.saved
    except Exception as e:
        messagebox.showerror("Error", f"Failed to create settings window: {e}")
        return False