# ui.py
import tkinter as tk
from tkinter import ttk


class UI:
    """
    Creates and manages all the UI widgets for the main application window.
    This class is responsible for the layout and does not contain application logic.
    """
    def __init__(self, root, callbacks, root_dir_var):
        self.root = root
        self.callbacks = callbacks
        self.root_dir_var = root_dir_var
        self.animation_running = False
        
        self._create_menu()
        self.create_widgets()
        self._setup_animations()
        self._setup_hover_effects()

    def _create_menu(self):
        """Creates the main menu bar for the application."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # --- File Menu ---
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Select Folder...", command=self.callbacks['select_folder'])
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.callbacks['exit'])

        # --- Edit Menu ---
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Check All", command=self.callbacks['check_all'])
        edit_menu.add_command(label="Uncheck All", command=self.callbacks['uncheck_all'])

        # --- Settings Menu ---
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Preferences...", command=self.callbacks['show_settings'])

        # --- Help Menu ---
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.callbacks['show_about'])

    def create_widgets(self):
        """Creates and lays out all the widgets in the main window."""
        # Configure style for better appearance
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Segoe UI', 12, 'bold'))
        style.configure('Status.TLabel', font=('Segoe UI', 9))
        style.configure('Action.TButton', font=('Segoe UI', 10, 'bold'))

        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)  # Tree container should expand

        # --- Header with App Title (Row 0) ---
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        title_label = ttk.Label(header_frame, text="Codebase to Text Converter", style="Title.TLabel")
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = ttk.Label(header_frame, text="Convert your codebase to LLM-ready markdown",
                                 foreground="gray", font=('Segoe UI', 9))
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0))

        # --- Control Frame (Row 1) ---
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        control_frame.grid_columnconfigure(1, weight=1)

        self.open_folder_button = ttk.Button(control_frame, text="Add Root Folder",
                                           command=self.callbacks['select_folder'])
        self.open_folder_button.grid(row=0, column=0, padx=(0, 5))

        self.folder_entry = ttk.Entry(control_frame, textvariable=self.root_dir_var,
                                    state='readonly', font=('Segoe UI', 9))
        self.folder_entry.grid(row=0, column=1, sticky="ew", padx=5)

        self.generate_button = ttk.Button(control_frame, text="Generate Text",
                                        command=self.callbacks['start_conversion'],
                                        style="Accent.TButton", state='disabled')
        self.generate_button.grid(row=0, column=2, padx=5)

        self.cancel_button = ttk.Button(control_frame, text="Cancel",
                                      command=self.callbacks['cancel_operation'], state='disabled')
        self.cancel_button.grid(row=0, column=3, padx=(5, 0))

        # --- Treeview Frame (Row 2) ---
        tree_container = ttk.LabelFrame(main_frame, text="📋 Select Files and Folders", padding="10")
        tree_container.grid(row=2, column=0, sticky="nsew")
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        tree_frame = ttk.Frame(tree_container)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(tree_frame, show="tree", style="Treeview")
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        style.configure("Treeview", font=('Segoe UI', 9), rowheight=25)
        style.configure("Treeview.Heading", font=('Segoe UI', 9, 'bold'))
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # --- Treeview Control Buttons ---
        button_control_frame = ttk.Frame(tree_container)
        button_control_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        button_control_frame.grid_columnconfigure(3, weight=1) # Give extra space to the right
        
        self.check_all_btn = ttk.Button(button_control_frame, text="✓ Check All",
                                       command=self.callbacks['check_all'], style="Action.TButton")
        self.check_all_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        self.uncheck_all_btn = ttk.Button(button_control_frame, text="☐ Uncheck All",
                                         command=self.callbacks['uncheck_all'], style="Action.TButton")
        self.uncheck_all_btn.grid(row=0, column=1, sticky="ew", padx=5)
        
        self.refresh_btn = ttk.Button(button_control_frame, text="🔄 Refresh",
                                     command=self._refresh_tree, style="Action.TButton")
        self.refresh_btn.grid(row=0, column=2, sticky="ew", padx=(5, 15))

        # Sorting controls
        sort_label = ttk.Label(button_control_frame, text="Sort by:")
        sort_label.grid(row=0, column=4, padx=(10, 5))
        
        self.sort_var = tk.StringVar(value="Name")
        self.sort_combo = ttk.Combobox(button_control_frame, textvariable=self.sort_var,
                                     values=['Name', 'Lines', 'Characters'], state='readonly', width=12)
        self.sort_combo.grid(row=0, column=5)
        self.sort_combo.bind("<<ComboboxSelected>>", lambda e: self.callbacks['sort_tree'](self.sort_var.get()))

        # --- Status Bar (Row 3) ---
        status_bar = ttk.Frame(main_frame, padding=(0, 5))
        status_bar.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        status_bar.grid_columnconfigure(0, weight=1)

        self.status_label = ttk.Label(status_bar, text="Ready", style="Status.TLabel", anchor="w")
        self.status_label.grid(row=0, column=0, sticky="ew")

        self.progress_bar = ttk.Progressbar(status_bar, orient='horizontal',
                                          mode='determinate', length=150)
        self.progress_bar.grid(row=0, column=1, sticky="ew", padx=(10, 0))

        self.progress_text = ttk.Label(status_bar, text="", style="Status.TLabel", anchor="w")
        self.progress_text.grid(row=0, column=2, sticky="w", padx=(5, 0))

    def _setup_animations(self):
        """Setup animation effects for UI elements."""
        self.animation_running = False
        
    def _setup_hover_effects(self):
        """Setup hover effects for interactive elements."""
        # Add hover effects to buttons
        for btn in [self.open_folder_button, self.check_all_btn, self.uncheck_all_btn,
                   self.refresh_btn, self.generate_button, self.cancel_button]:
            btn.bind('<Enter>', lambda e, b=btn: self._on_button_hover_enter(b))
            btn.bind('<Leave>', lambda e, b=btn: self._on_button_hover_leave(b))

    def _on_button_hover_enter(self, button):
        """Handle button hover enter event."""
        if button.cget('state') != 'disabled' and button != self.generate_button:
            button.configure(style='Accent.TButton')

    def _on_button_hover_leave(self, button):
        """Handle button hover leave event."""
        if button.cget('state') != 'disabled':
            button.configure(style='TButton')

    def _refresh_tree(self):
        """Refresh the tree view."""
        if hasattr(self, 'tree') and self.tree.get_children():
            # Animate refresh
            self._animate_refresh()
            # Call the refresh callback if available
            if 'refresh_tree' in self.callbacks:
                self.callbacks['refresh_tree']()

    def _animate_refresh(self):
        """Animate the refresh button."""
        if self.animation_running:
            return
            
        self.animation_running = True
        original_text = self.refresh_btn.cget('text')
        
        def animate_rotation(angle=0):
            if angle >= 360:
                self.refresh_btn.configure(text=original_text)
                self.animation_running = False
                return
            
            self.refresh_btn.configure(text="🔄")
            self.root.after(50, lambda: animate_rotation(angle + 45))
        
        animate_rotation()

    def update_progress(self, current, total):
        """Update progress bar with enhanced feedback."""
        if total > 0:
            percentage = (current / total) * 100
            self.progress_bar['value'] = percentage
            self.progress_text.configure(text=f"Progress: {current}/{total} ({percentage:.1f}%)")
        else:
            self.progress_bar['value'] = 0
            self.progress_text.configure(text="")

    def update_status(self, message):
        """Update status with enhanced formatting."""
        self.status_label.configure(text=message)
        
        # Add visual feedback for different status types
        if "error" in message.lower():
            self.status_label.configure(foreground="red")
        elif "complete" in message.lower():
            self.status_label.configure(foreground="green")
        elif "scanning" in message.lower() or "generating" in message.lower():
            self.status_label.configure(foreground="blue")
        else:
            self.status_label.configure(foreground="")

    def show_loading_state(self, loading=True):
        """Show/hide loading state for buttons."""
        if loading:
            self.generate_button.configure(state='disabled', text="⏳ Processing...")
            self.open_folder_button.configure(state='disabled')
            self.check_all_btn.configure(state='disabled')
            self.uncheck_all_btn.configure(state='disabled')
            self.refresh_btn.configure(state='disabled')
        else:
            self.generate_button.configure(state='normal', text="Generate Text")
            self.open_folder_button.configure(state='normal')
            self.check_all_btn.configure(state='normal')
            self.uncheck_all_btn.configure(state='normal')
            self.refresh_btn.configure(state='normal')

    def show_success_animation(self):
        """Show a brief success animation."""
        self.generate_button.configure(text="✅ Success!")
        self.root.after(1500, lambda: self.generate_button.configure(text="Generate Text"))