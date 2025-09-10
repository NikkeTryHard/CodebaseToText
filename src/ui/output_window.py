# output_window.py
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import time

# Lowered limit to prevent slow inserts in Tkinter for large outputs
OUTPUT_CHARACTER_LIMIT = 1_000_000

class EnhancedOutputWindow:
    """Enhanced output window with better UI and functionality."""
    
    def __init__(self, parent_root, content, log_callback, config_manager):
        self.parent_root = parent_root
        self.content = content
        self.log_callback = log_callback
        self.config = config_manager
        self.animation_running = False
        
        self.output_win = tk.Toplevel(parent_root)
        self.output_win.title("Generated Output (LLM-Ready Markdown)")
        
        # Get geometry from config or use default
        geometry = self.config.get_setting('Settings', 'output_window_geometry', fallback="1000x800")
        self.output_win.geometry(geometry)
        self.output_win.minsize(800, 600)
        
        # Center the window
        self._center_window()
        
        # Setup window behavior
        self.output_win.transient(parent_root)
        self.output_win.grab_set()
        self.output_win.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Create UI
        self._create_ui()
        self._setup_animations()
        
        # Load content
        self._load_content()

    def _center_window(self):
        """Center the window relative to the parent."""
        try:
            parent_x = self.parent_root.winfo_x()
            parent_y = self.parent_root.winfo_y()
            parent_width = self.parent_root.winfo_width()
            parent_height = self.parent_root.winfo_height()
            
            win_width = 1000
            win_height = 800
            x = parent_x + (parent_width // 2) - (win_width // 2)
            y = parent_y + (parent_height // 2) - (win_height // 2)
            self.output_win.geometry(f"{win_width}x{win_height}+{x}+{y}")
        except:
            # Fallback centering
            self.output_win.geometry("1000x800")

    def _create_ui(self):
        """Create the enhanced UI."""
        # Configure styles
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Segoe UI', 14, 'bold'))
        style.configure('Status.TLabel', font=('Segoe UI', 9))
        style.configure('Action.TButton', font=('Segoe UI', 10, 'bold'))
        
        # Main container
        main_frame = ttk.Frame(self.output_win, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = ttk.Label(header_frame, text="📄 Generated Output", style="Title.TLabel")
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = ttk.Label(header_frame, text="Your codebase converted to LLM-ready markdown", 
                                 foreground="gray", font=('Segoe UI', 9))
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Top controls frame
        controls_frame = ttk.LabelFrame(main_frame, text="Actions", padding="10")
        controls_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Left side controls
        left_controls = ttk.Frame(controls_frame)
        left_controls.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.copy_button = ttk.Button(
            left_controls,
            text="📋 Copy All to Clipboard",
            style="Action.TButton",
            command=self._copy_to_clipboard
        )
        self.copy_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.save_button = ttk.Button(
            left_controls,
            text="💾 Save to File",
            style="Action.TButton",
            command=self._save_to_file
        )
        self.save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Right side controls
        right_controls = ttk.Frame(controls_frame)
        right_controls.pack(side=tk.RIGHT)
        
        self.close_button = ttk.Button(
            right_controls, 
            text="❌ Close", 
            command=self.output_win.destroy
        )
        self.close_button.pack(side=tk.RIGHT)
        
        # Status frame
        status_frame = ttk.Frame(controls_frame)
        status_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(20, 0))
        
        self.status_label = ttk.Label(status_frame, text="Ready", style="Status.TLabel")
        self.status_label.pack(side=tk.LEFT)
        
        # Progress frame for large files
        self.progress_frame = ttk.Frame(controls_frame)
        self.progress_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(20, 0))
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient='horizontal', 
                                          mode='determinate', length=200)
        self.progress_text = ttk.Label(self.progress_frame, text="", style="Status.TLabel")
        
        # Content frame
        content_frame = ttk.LabelFrame(main_frame, text="Content", padding="10")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Enhanced text widget
        self.content_text = scrolledtext.ScrolledText(
            content_frame,
            wrap=tk.WORD,
            state='normal',
            font=("Consolas", 10),
            padx=15,
            pady=15,
            undo=False,  # Disable undo for faster large inserts
            selectbackground="#0078d4",
            selectforeground="white"
        )
        self.content_text.pack(fill=tk.BOTH, expand=True)
        
        # Bottom info frame
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.info_label = ttk.Label(info_frame, text="", style="Status.TLabel", foreground="gray")
        self.info_label.pack(side=tk.LEFT)

    def _setup_animations(self):
        """Setup animation effects."""
        self.animation_running = False

    def _load_content(self):
        """Load content into the text widget with enhanced handling."""
        try:
            content_length = len(self.content)
            
            if content_length > OUTPUT_CHARACTER_LIMIT:
                self._handle_large_content()
            else:
                self._insert_content_directly()
                
            # Update info
            self._update_info(content_length)
            
        except Exception as e:
            self.log_callback(f"Error loading content: {e}")
            messagebox.showerror("Error", f"Failed to load content: {e}")

    def _handle_large_content(self):
        """Handle large content by saving to file and showing message."""
        try:
            # Save to desktop
            desktop_path = self._get_desktop_path()
            output_path = os.path.join(desktop_path, "CodebaseToText_Output.md")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(self.content)
            
            # Show success message
            message = (
                f"📊 Output is very large ({len(self.content):,} characters)\n\n"
                f"✅ Automatically saved to:\n"
                f"📁 {output_path}\n\n"
                f"💡 You can now open this file in your preferred text editor."
            )
            
            self.content_text.insert('1.0', message)
            self.content_text.config(state='disabled')
            
            # Disable copy button for large files
            self.copy_button.config(state='disabled')
            self.save_button.config(state='disabled')
            
            # Show progress info
            self.progress_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(20, 0))
            self.progress_bar.pack(side=tk.LEFT, padx=(0, 10))
            self.progress_text.pack(side=tk.LEFT)
            
            self.progress_bar['value'] = 100
            self.progress_text.config(text="Saved to Desktop")
            
            self.log_callback(f"Large output saved to {output_path}")
            
        except Exception as e:
            error_message = f"❌ Error saving large output:\n\n{str(e)}"
            self.content_text.insert('1.0', error_message)
            self.content_text.config(state='disabled')
            self.log_callback(f"Error saving large output: {e}")

    def _insert_content_directly(self):
        """Insert content directly into the text widget."""
        try:
            # Show progress for large content
            if len(self.content) > 100000:  # 100KB threshold
                self._show_insert_progress()
            else:
                # Direct insert for smaller content
                self.content_text.insert('1.0', self.content)
                self.content_text.config(state='disabled')
                
        except Exception as e:
            self.log_callback(f"Error inserting content: {e}")
            messagebox.showerror("Error", f"Failed to insert content: {e}")

    def _show_insert_progress(self):
        """Show progress while inserting large content."""
        self.progress_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(20, 0))
        self.progress_bar.pack(side=tk.LEFT, padx=(0, 10))
        self.progress_text.pack(side=tk.LEFT)
        
        # Insert content in chunks
        chunk_size = 50000  # 50KB chunks
        total_chunks = (len(self.content) + chunk_size - 1) // chunk_size
        
        def insert_chunk(chunk_index=0):
            if chunk_index >= total_chunks:
                # Finished inserting
                self.content_text.config(state='disabled')
                self.progress_bar['value'] = 100
                self.progress_text.config(text="Complete")
                return
            
            start = chunk_index * chunk_size
            end = min(start + chunk_size, len(self.content))
            chunk = self.content[start:end]
            
            try:
                self.content_text.insert(tk.END, chunk)
                
                # Update progress
                progress = ((chunk_index + 1) / total_chunks) * 100
                self.progress_bar['value'] = progress
                self.progress_text.config(text=f"Inserting... {chunk_index + 1}/{total_chunks}")
                
                # Schedule next chunk
                self.output_win.after(10, lambda: insert_chunk(chunk_index + 1))
                
            except Exception as e:
                self.log_callback(f"Error inserting chunk {chunk_index}: {e}")
                self.progress_text.config(text="Error inserting content")
        
        insert_chunk()

    def _get_desktop_path(self):
        """Get the desktop path for the current user."""
        try:
            if os.name == 'nt':  # Windows
                return os.path.join(os.path.expanduser("~"), "Desktop")
            else:  # macOS/Linux
                return os.path.join(os.path.expanduser("~"), "Desktop")
        except:
            # Fallback to current directory
            return os.getcwd()

    def _copy_to_clipboard(self):
        """Copy content to clipboard with enhanced feedback."""
        try:
            content = self.content_text.get('1.0', tk.END)
            if not content.strip():
                self._show_status("Nothing to copy", "red")
                return
                
            self.output_win.clipboard_clear()
            self.output_win.clipboard_append(content)
            
            self._show_status("✅ Copied to clipboard!", "green")
            self.log_callback("Content copied to clipboard")
            
            # Animate copy button
            self._animate_copy_success()
            
        except Exception as e:
            self._show_status("❌ Copy failed", "red")
            self.log_callback(f"Could not copy to clipboard: {e}")

    def _save_to_file(self):
        """Save content to a file with file dialog."""
        try:
            from tkinter import filedialog
            
            # Get file path from user
            file_path = filedialog.asksaveasfilename(
                defaultextension=".md",
                filetypes=[
                    ("Markdown files", "*.md"),
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ],
                title="Save Output As"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.content)
                
                self._show_status(f"✅ Saved to {os.path.basename(file_path)}", "green")
                self.log_callback(f"Content saved to {file_path}")
                
                # Animate save button
                self._animate_save_success()
                
        except Exception as e:
            self._show_status("❌ Save failed", "red")
            self.log_callback(f"Could not save file: {e}")

    def _show_status(self, message, color="black"):
        """Show status message with color."""
        self.status_label.config(text=message, foreground=color)
        
        # Reset color after delay
        self.output_win.after(3000, lambda: self.status_label.config(foreground="black"))

    def _animate_copy_success(self):
        """Animate copy button on success."""
        if self.animation_running:
            return
            
        self.animation_running = True
        original_text = self.copy_button.cget('text')
        
        def animate():
            self.copy_button.configure(text="✅ Copied!")
            self.output_win.after(1000, lambda: self._reset_button_text(self.copy_button, original_text))
        
        animate()

    def _animate_save_success(self):
        """Animate save button on success."""
        if self.animation_running:
            return
            
        self.animation_running = True
        original_text = self.save_button.cget('text')
        
        def animate():
            self.save_button.configure(text="✅ Saved!")
            self.output_win.after(1000, lambda: self._reset_button_text(self.save_button, original_text))
        
        animate()

    def _reset_button_text(self, button, text):
        """Reset button text after animation."""
        button.configure(text=text)
        self.animation_running = False

    def _update_info(self, content_length):
        """Update information display."""
        try:
            # Calculate file size
            size_kb = content_length / 1024
            if size_kb > 1024:
                size_str = f"{size_kb/1024:.1f} MB"
            else:
                size_str = f"{size_kb:.1f} KB"
            
            # Count lines
            line_count = self.content.count('\n') + 1
            
            info_text = f"📊 {content_length:,} characters • {line_count:,} lines • {size_str}"
            self.info_label.config(text=info_text)
            
        except Exception as e:
            self.log_callback(f"Error updating info: {e}")

    def on_close(self):
        """Handle window closing."""
        try:
            # Save geometry
            self.config.set_setting('Settings', 'output_window_geometry', self.output_win.geometry())
            self.config.save_config()
        except Exception as e:
            self.log_callback(f"Error saving output window geometry: {e}")
        finally:
            self.output_win.destroy()

def show_output_window(parent_root, content, log_callback, config_manager):
    """Creates and displays the enhanced output window."""
    try:
        window = EnhancedOutputWindow(parent_root, content, log_callback, config_manager)
        return window
    except Exception as e:
        log_callback(f"Error creating output window: {e}")
        messagebox.showerror("Error", f"Failed to create output window: {e}")
        return None