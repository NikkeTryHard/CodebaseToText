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
        
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_rowconfigure(2, weight=1)  # Make the treeview frame expandable
        main_frame.grid_columnconfigure(0, weight=1)

        # --- Header with App Title ---
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        title_label = ttk.Label(header_frame, text="Codebase to Text Converter", style="Title.TLabel")
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = ttk.Label(header_frame, text="Convert your codebase to LLM-ready markdown", 
                                 foreground="gray", font=('Segoe UI', 9))
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0))

        # --- Folder Selection Frame ---
        folder_frame = ttk.LabelFrame(main_frame, text="📁 Select Root Folder", padding="15")
        folder_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        folder_frame.grid_columnconfigure(0, weight=1)
        
        # Create a simple button frame for better visibility
        button_frame = ttk.Frame(folder_frame)
        button_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        button_frame.grid_columnconfigure(0, weight=1)
        
        # Large, prominent Open Folder button - make it impossible to miss!
        self.open_folder_button = ttk.Button(button_frame, text="Add Root Folder",
                                           command=self.callbacks['select_folder'])
        self.open_folder_button.grid(row=0, column=0, sticky="ew", ipady=10)
        
        # Folder path display section
        path_label = ttk.Label(folder_frame, text="Selected folder:", font=('Segoe UI', 9, 'bold'))
        path_label.grid(row=1, column=0, sticky="w", pady=(0, 5))
        
        path_frame = ttk.Frame(folder_frame)
        path_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        path_frame.grid_columnconfigure(0, weight=1)
        
        self.folder_entry = ttk.Entry(path_frame, textvariable=self.root_dir_var, 
                                    state='readonly', font=('Segoe UI', 9))
        self.folder_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        # Alternative browse button (smaller)
        self.browse_button = ttk.Button(path_frame, text="Browse...", 
                                      command=self.callbacks['select_folder'])
        self.browse_button.grid(row=0, column=1)
        
        # Drag and drop hint
        drop_hint = ttk.Label(folder_frame, text="💡 Tip: You can also drag and drop a folder here", 
                            foreground="gray", font=('Segoe UI', 8))
        drop_hint.grid(row=3, column=0, sticky="w", pady=(5, 0))

        # --- Treeview Frame ---
        tree_container = ttk.LabelFrame(main_frame, text="📋 Select Files and Folders", padding="15")
        tree_container.grid(row=2, column=0, sticky="nsew", pady=(0, 15))
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        tree_frame = ttk.Frame(tree_container)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Enhanced treeview with better styling
        self.tree = ttk.Treeview(tree_frame, show="tree", style="Treeview")
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        # Configure treeview style
        style.configure("Treeview", font=('Segoe UI', 9), rowheight=25)
        style.configure("Treeview.Heading", font=('Segoe UI', 9, 'bold'))
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # --- Treeview Control Buttons ---
        button_control_frame = ttk.Frame(tree_container)
        button_control_frame.grid(row=1, column=0, sticky="ew", pady=(15, 0))
        button_control_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Enhanced buttons with icons and better styling
        self.check_all_btn = ttk.Button(button_control_frame, text="✓ Check All", 
                                       command=self.callbacks['check_all'], style="Action.TButton")
        self.check_all_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        self.uncheck_all_btn = ttk.Button(button_control_frame, text="☐ Uncheck All", 
                                         command=self.callbacks['uncheck_all'], style="Action.TButton")
        self.uncheck_all_btn.grid(row=0, column=1, sticky="ew", padx=5)
        
        # Add a refresh button
        self.refresh_btn = ttk.Button(button_control_frame, text="🔄 Refresh", 
                                     command=self._refresh_tree, style="Action.TButton")
        self.refresh_btn.grid(row=0, column=2, sticky="ew", padx=(5, 0))

        # --- Action Frame ---
        action_frame = ttk.LabelFrame(main_frame, text="🚀 Generate Output", padding="15")
        action_frame.grid(row=3, column=0, sticky="ew")
        
        # --- Button Container ---
        button_container = ttk.Frame(action_frame)
        button_container.pack(fill=tk.X, pady=(10, 0))
        button_container.grid_columnconfigure(0, weight=1)
        button_container.grid_columnconfigure(1, weight=1)

        self.generate_button = ttk.Button(button_container, text="🎯 Generate Text", 
                                        command=self.callbacks['start_conversion'], 
                                        style="Accent.TButton", state='disabled')
        self.generate_button.grid(row=0, column=0, sticky="ew", padx=(0, 5), ipady=8)

        self.cancel_button = ttk.Button(button_container, text="❌ Cancel", 
                                      command=self.callbacks['cancel_operation'])
        self.cancel_button.grid(row=0, column=1, sticky="ew", padx=(5, 0), ipady=8)
        self.cancel_button.config(state='disabled')

        # Enhanced status and progress
        status_frame = ttk.Frame(action_frame)
        status_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.status_label = ttk.Label(status_frame, text="Ready to scan directory", 
                                    style="Status.TLabel", anchor="w")
        self.status_label.pack(fill=tk.X, pady=(0, 5))

        # Enhanced progress bar with better styling
        progress_frame = ttk.Frame(action_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(progress_frame, orient='horizontal', 
                                          mode='determinate', length=300)
        self.progress_bar.pack(fill=tk.X)
        
        # Progress text
        self.progress_text = ttk.Label(progress_frame, text="", style="Status.TLabel", anchor="center")
        self.progress_text.pack(fill=tk.X, pady=(2, 0))

    def _setup_animations(self):
        """Setup animation effects for UI elements."""
        self.animation_running = False
        
    def _setup_hover_effects(self):
        """Setup hover effects for interactive elements."""
        # Add hover effects to buttons
        for btn in [self.open_folder_button, self.browse_button, self.check_all_btn, self.uncheck_all_btn,
                   self.refresh_btn, self.generate_button, self.cancel_button]:
            btn.bind('<Enter>', lambda e, b=btn: self._on_button_hover_enter(b))
            btn.bind('<Leave>', lambda e, b=btn: self._on_button_hover_leave(b))

    def _on_button_hover_enter(self, button):
        """Handle button hover enter event."""
        if button.cget('state') != 'disabled':
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
            self.browse_button.configure(state='disabled')
            self.check_all_btn.configure(state='disabled')
            self.uncheck_all_btn.configure(state='disabled')
            self.refresh_btn.configure(state='disabled')
        else:
            self.generate_button.configure(state='normal', text="🎯 Generate Text")
            self.open_folder_button.configure(state='normal')
            self.browse_button.configure(state='normal')
            self.check_all_btn.configure(state='normal')
            self.uncheck_all_btn.configure(state='normal')
            self.refresh_btn.configure(state='normal')

    def show_success_animation(self):
        """Show a brief success animation."""
        original_text = self.generate_button.cget('text')
        self.generate_button.configure(text="✅ Success!")
        self.root.after(1500, lambda: self.generate_button.configure(text=original_text))