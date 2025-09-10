# main.py
import sys
import os
import traceback
from tkinterdnd2 import TkinterDnD
from main_app import main as main_app
import argparse

def setup_environment():
    """Setup the environment for the application."""
    try:
        # Add current directory to Python path for imports
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
            
        # Set up environment variables if needed
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        
    except Exception as e:
        print(f"Error setting up environment: {e}")

def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler for unhandled exceptions."""
    if issubclass(exc_type, KeyboardInterrupt):
        # Handle Ctrl+C gracefully
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
        
    # Log the error
    error_msg = f"Unhandled exception: {exc_type.__name__}: {exc_value}"
    print(error_msg)
    
    # Print traceback for debugging
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    
    # Try to show error dialog if tkinter is available
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        messagebox.showerror(
            "Application Error", 
            f"An unexpected error occurred:\n\n{error_msg}\n\n"
            "Please check the console for more details.\n"
            "If this error persists, please report it."
        )
        root.destroy()
        
    except:
        pass  # If we can't show dialog, just continue

def main():
    """
    Initializes and runs the enhanced DirectoryToTextApp application.
    """
    try:
        # Setup environment
        setup_environment()
        
        # Set up global exception handler
        sys.excepthook = handle_exception
        
        # Parse command line arguments
        parser = argparse.ArgumentParser(
            description="Convert a directory structure to a single text file for LLMs - Enhanced Edition",
            epilog="Enhanced with better UI, animations, and error handling"
        )
        parser.add_argument("-v", "--verbose", action="store_true", 
                          help="Enable verbose output to the terminal")
        parser.add_argument("--debug", action="store_true", 
                          help="Enable debug mode with additional logging")
        parser.add_argument("--config", type=str, 
                          help="Path to custom configuration file")
        
        args = parser.parse_args()
        
        # Set debug environment variable if requested
        if args.debug:
            os.environ['DEBUG'] = '1'
            print("Debug mode enabled")
        
        print("🚀 Starting CodebaseToText v7.4 - Enhanced Edition")
        print("✨ Enhanced UI with animations and better UX")
        print("🛡️ Improved error handling and robustness")
        
        # Run the application
        main_app(args)
        
        print("👋 Application closed successfully")
        
    except KeyboardInterrupt:
        print("\n⚠️ Application interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error during application startup: {e}")
        traceback.print_exc()
        
        # Try to show error dialog
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            root = tk.Tk()
            root.withdraw()
            
            messagebox.showerror(
                "Startup Error", 
                f"Failed to start the application:\n\n{str(e)}\n\n"
                "Please check the console for more details."
            )
            root.destroy()
            
        except:
            pass
        
        sys.exit(1)

if __name__ == "__main__":
    main()