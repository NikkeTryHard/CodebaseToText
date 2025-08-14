# file_processor.py
import os
import traceback
from constants import LANGUAGE_MAP, MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB

class FileProcessingError(Exception):
    """Base class for file processing errors."""
    pass

class FileTooLargeError(FileProcessingError):
    """Raised when a file is too large to process."""
    pass

class BinaryFileError(FileProcessingError):
    """Raised when a file is identified as binary."""
    pass

def get_all_files(directory):
    """
    Recursively gets all file paths in a directory.

    Args:
        directory (str): The path to the directory.

    Returns:
        list: A list of full file paths.
    """
    all_files = []
    for root, _, files in os.walk(directory):
        for name in files:
            all_files.append(os.path.join(root, name))
    return all_files

# In file_processor.py, function _is_binary_file
def _is_binary_file(filepath, chunk_size=1024):
    """Heuristically check if a file is binary by looking for null bytes."""
    try:
        with open(filepath, 'rb') as f:
            return b'\0' in f.read(chunk_size)
    except (IOError, PermissionError): # More specific exception handling
        return True

def _get_line_count(filepath):
    """Count lines in a text file, returning 0 for binary or unreadable files."""
    if _is_binary_file(filepath):
        return 0
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except (OSError, UnicodeDecodeError):
        return 0

def get_language_identifier(file_path):
    """
    Gets the language identifier for a file path.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The language identifier (e.g., 'python', 'javascript').
    """
    filename = os.path.basename(file_path)
    _, ext = os.path.splitext(filename)
    if filename.lower() in LANGUAGE_MAP:
        return LANGUAGE_MAP[filename.lower()]
    if ext.lower() in LANGUAGE_MAP:
        return LANGUAGE_MAP[ext.lower()]
    return 'text'

def build_annotated_tree(root_path, files_for_tree, files_for_content):
    """
    Builds a string representation of the directory tree with annotations.

    Args:
        root_path (str): The root path of the directory.
        files_for_tree (list): A list of all files to include in the tree structure.
        files_for_content (list): A list of files whose content will be included.

    Returns:
        str: A string representing the annotated directory tree.
    """
    tree_dict = {}
    base_dir = os.path.dirname(root_path)
    
    content_set = {os.path.normcase(os.path.abspath(p)) for p in files_for_content}

    all_paths = set(files_for_tree)
    for p in files_for_content:
        all_paths.add(p)

    for path in all_paths:
        relative_path = os.path.relpath(path, base_dir).replace(os.sep, '/')
        parts = relative_path.split('/')
        current_level = tree_dict
        for part in parts:
            current_level = current_level.setdefault(part, {})
    
    def generate_lines(d, prefix="", current_path=""):
        lines = []
        items = sorted(d.keys(), key=lambda name: (not d[name], name.lower()))
        for i, name in enumerate(items):
            connector = "└── " if i == len(items) - 1 else "├── "
            
            item_full_path_str = os.path.join(base_dir, current_path, name)
            item_normalized_path = os.path.normcase(os.path.abspath(item_full_path_str))
            
            annotation = ""
            is_file = not d[name]
            if is_file:
                annotations = []
                # FIX: Corrected the annotation logic to avoid redundant messages.
                if _is_binary_file(item_normalized_path):
                    annotations.append("binary file")
                    # If it's binary, it might also be omitted, but "binary file" is more specific.
                    if item_normalized_path not in content_set:
                        annotations.append("content omitted")
                else:
                    # Handle as a text file
                    line_count = _get_line_count(item_normalized_path)
                    if line_count > 0:
                        annotations.append(f"{line_count} lines")
                    
                    if item_normalized_path not in content_set:
                        annotations.append("content omitted")
                
                if annotations:
                    annotation = f"  [{' | '.join(annotations)}]"

            lines.append(f"{prefix}{connector}{name}{annotation}")

            if d[name]:
                extension = "    " if i == len(items) - 1 else "│   "
                new_path = os.path.join(current_path, name)
                lines.extend(generate_lines(d[name], prefix + extension, new_path))
        return lines
    
    root_folder_name = os.path.basename(root_path)
    tree_lines = [root_folder_name]
    tree_lines.extend(generate_lines(tree_dict.get(root_folder_name, {}), "", root_folder_name))
    return "\n".join(tree_lines)


def generate_text_content(root_path, files_for_tree, files_for_content, log_callback, success_callback, final_callback, progress_callback=None):
    """
    Generates the final text output with directory structure and file contents.
    This function is designed to be run in a separate thread.
    """
    try:
        final_content = []
        base_path_for_relpath = os.path.dirname(root_path)

        log_callback("\n--- Building Annotated Directory Tree ---")
        tree_structure = build_annotated_tree(root_path, files_for_tree, files_for_content)
        
        final_content.append("# Codebase Structure and File Contents\n\n")
        final_content.append("## Project Structure\n\n```text\n")
        final_content.append(tree_structure)
        final_content.append("\n```\n\n---\n\n## File Contents\n\n")

        log_callback("\n--- Processing Selected File Contents into Markdown ---")
        for file_path in sorted(files_for_content):
            relative_path = os.path.relpath(file_path, base_path_for_relpath).replace(os.sep, '/')

            try:
                # Perform checks first
                file_size = os.path.getsize(file_path)
                if file_size > MAX_FILE_SIZE_BYTES:
                    raise FileTooLargeError(f"File is larger than {MAX_FILE_SIZE_MB}MB")
                if _is_binary_file(file_path):
                    raise BinaryFileError("File is binary")

                # If checks pass, read the file
                log_callback(f"Adding content for: {relative_path}")
                language = get_language_identifier(file_path)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                final_content.extend([f"### `{relative_path}`\n\n", f"```{language}\n", content, "\n```\n\n"])

            except (OSError, FileProcessingError) as e:
                log_callback(f"Skipping '{relative_path}': {e}")
                final_content.extend([f"### `{relative_path}`\n\n```text\n--- CONTENT SKIPPED: {e} ---\n```\n\n"])
            
            final_content.append("---\n\n")
            if progress_callback:
                progress_callback()

        success_callback("".join(final_content))
    except Exception as e:
        log_callback(f"An unexpected error occurred during generation: {e}")
        log_callback(f"Traceback:\n{traceback.format_exc()}")
    finally:
        final_callback()