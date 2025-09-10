# main_app.py
import tkinter as tk
from tkinterdnd2 import TkinterDnD
from app_logic import DirectoryToTextApp

def main(args):
    """
    Initializes and runs the DirectoryToTextApp application.
    """
    root = TkinterDnD.Tk()
    app = DirectoryToTextApp(
        root,
        verbose=args.verbose,
        config_file=args.config
    )
    root.mainloop()