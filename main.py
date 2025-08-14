# main.py
from tkinterdnd2 import TkinterDnD
from main_app import DirectoryToTextApp
import argparse

def main():
    """
    Initializes and runs the DirectoryToTextApp application.
    """
    # Add command-line argument parsing for verbose mode
    parser = argparse.ArgumentParser(description="Convert a directory structure to a single text file for LLMs.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output to the terminal.")
    args = parser.parse_args()

    root = TkinterDnD.Tk()
    
    # Pass verbose flag to the app and remove unused 'app' variable assignment
    DirectoryToTextApp(root, verbose=args.verbose)
    
    root.mainloop()

if __name__ == "__main__":
    main()