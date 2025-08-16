# output_window.py
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os

# Set a character limit to prevent the app from freezing on huge outputs
# 5 million characters is roughly 5 MB, a safe limit for Tkinter.
OUTPUT_CHARACTER_LIMIT = 5_000_000

def _copy_to_clipboard(root, text_widget, status_label, log_callback):
    """Copies the content of the text widget to the system clipboard."""
    try:
        content = text_widget.get('1.0', tk.END)
        root.clipboard_clear()
        root.clipboard_append(content)
        status_label.config(text="Copied to clipboard!", foreground="green")
        log_callback("Content copied to clipboard.")
        root.after(2000, lambda: status_label.config(text="Ready.", foreground=""))
    except tk.TclError:
        log_callback("Could not copy to clipboard (maybe empty).")
        status_label.config(text="Nothing to copy.", foreground="red")
        root.after(2000, lambda: status_label.config(text="Ready.", foreground=""))

def show_output_window(parent_root, content, log_callback):
    """Creates and displays the output window."""
    output_win = tk.Toplevel(parent_root)
    output_win.title("Generated Output (LLM-Ready Markdown)")
    output_win.geometry("900x700")

    # --- Top Frame for Controls ---
    top_frame = ttk.Frame(output_win, padding=10)
    top_frame.pack(fill=tk.X)

    copy_button = ttk.Button(
        top_frame,
        text="Copy All to Clipboard",
        style="Accent.TButton"
    )
    copy_button.pack(side=tk.LEFT, padx=(0, 10))
    
    status_label = ttk.Label(top_frame, text="Ready.")
    status_label.pack(side=tk.LEFT)
    
    close_button = ttk.Button(top_frame, text="Close", command=output_win.destroy)
    close_button.pack(side=tk.RIGHT)

    # --- ScrolledText for Content ---
    content_text = scrolledtext.ScrolledText(
        output_win,
        wrap=tk.WORD,
        state='normal',
        font=("Courier New", 10),
        padx=10,
        pady=10
    )
    content_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    # <<< FIX: Handle potentially huge content to prevent freezing
    if len(content) > OUTPUT_CHARACTER_LIMIT:
        try:
            desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        except:
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        
        output_path = os.path.join(desktop, "CodebaseToText_Output.txt")
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            message = (f"The output is too large to display safely ({len(content):,} characters).\n\n"
                       f"It has been automatically saved to your Desktop as:\n\n"
                       f"{output_path}")
            content_text.insert('1.0', message)
            log_callback(f"Output too large, saved to {output_path}")
            copy_button.config(state='disabled') # Disable copy button as content is not in widget
        except Exception as e:
            message = f"The output is too large to display, and an error occurred while saving it to the desktop:\n\n{e}"
            content_text.insert('1.0', message)
            log_callback(f"Error saving large output file: {e}")
            copy_button.config(state='disabled')
    else:
        content_text.insert('1.0', content)
    
    content_text.config(state='disabled')
    
    # --- Bind Command After Widget Creation ---
    copy_button['command'] = lambda: _copy_to_clipboard(parent_root, content_text, status_label, log_callback)

    # --- Window Behavior ---
    output_win.transient(parent_root)
    output_win.grab_set()
    parent_root.wait_window(output_win)