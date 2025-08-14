# ui.py
import tkinter as tk
from tkinter import ttk

class UI:
    """
    Creates and manages all the UI widgets for the main application window.
    This class is responsible for the layout and does not contain application logic.
    """
    def __init__(self, root, callbacks, root_dir_var, include_all_var):
        self.root = root
        self.callbacks = callbacks
        self.root_dir_var = root_dir_var
        self.include_all_var = include_all_var
        
        self._create_menu()
        self.create_widgets()

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

        # --- Help Menu ---
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.callbacks['show_about'])

    def create_widgets(self):
        """Creates and lays out all the widgets in the main window."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # --- Folder Selection Frame ---
        folder_frame = ttk.LabelFrame(main_frame, text="1. Select Root Folder", padding="10")
        folder_frame.grid(row=0, column=0, sticky="ew", pady=5)
        folder_frame.grid_columnconfigure(0, weight=1)
        ttk.Entry(folder_frame, textvariable=self.root_dir_var, state='readonly').grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ttk.Button(folder_frame, text="Browse...", command=self.callbacks['select_folder']).grid(row=0, column=1)

        # --- Treeview Frame ---
        tree_container = ttk.LabelFrame(main_frame, text="2. Select Files and Folders", padding="10")
        tree_container.grid(row=1, column=0, sticky="nsew", pady=5)
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        tree_frame = ttk.Frame(tree_container)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(tree_frame, show="tree")
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # --- Treeview Control Buttons ---
        button_control_frame = ttk.Frame(tree_container)
        button_control_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        button_control_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        ttk.Button(button_control_frame, text="Check Sel.", command=self.callbacks['check_selected']).grid(row=0, column=0, sticky="ew", padx=2)
        ttk.Button(button_control_frame, text="Uncheck Sel.", command=self.callbacks['uncheck_selected']).grid(row=0, column=1, sticky="ew", padx=2)
        ttk.Button(button_control_frame, text="Check All", command=self.callbacks['check_all']).grid(row=0, column=2, sticky="ew", padx=2)
        ttk.Button(button_control_frame, text="Uncheck All", command=self.callbacks['uncheck_all']).grid(row=0, column=3, sticky="ew", padx=2)

        # --- Action Frame ---
        action_frame = ttk.Frame(main_frame, padding=(0, 10))
        action_frame.grid(row=2, column=0, sticky="ew")
        
        self.include_all_toggle = ttk.Checkbutton(
            action_frame,
            text="Annotate Tree: Show all files in the directory structure.",
            variable=self.include_all_var,
            command=self.callbacks['toggle_include_all'],
            state='disabled'
        )
        self.include_all_toggle.pack(fill=tk.X, pady=(0, 5))

        self.run_button = ttk.Button(action_frame, text="Generate Text", command=self.callbacks['start_conversion'], style="Accent.TButton", state='disabled')
        self.run_button.pack(fill=tk.X, ipady=5)
        
        self.progress_bar = ttk.Progressbar(action_frame, orient='horizontal', mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))