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

def _is_binary_file(filepath, chunk_size=1024):
    """Heuristically check if a file is binary by looking for null bytes."""
    try:
        with open(filepath, 'rb') as f:
            return b'\0' in f.read(chunk_size)
    except (IOError, PermissionError):
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
    """
    filename = os.path.basename(file_path)
    _, ext = os.path.splitext(filename)
    if filename.lower() in LANGUAGE_MAP:
        return LANGUAGE_MAP[filename.lower()]
    if ext.lower() in LANGUAGE_MAP:
        return LANGUAGE_MAP[ext.lower()]
    return 'text'

def build_annotated_tree(root_path, files_for_tree, files_for_content, is_annotated_mode, ignored_items):
    """
    Builds a string representation of the directory tree with annotations.
    """
    tree_dict = {}
    base_dir = os.path.dirname(root_path)
    content_set = {os.path.normcase(os.path.abspath(p)) for p in files_for_content}

    for path in files_for_tree:
        relative_path = os.path.relpath(path, base_dir).replace(os.sep, '/')
        parts = relative_path.split('/')
        current_level = tree_dict
        for part in parts:
            # Stop processing if a part of the path is in the ignored set
            if part in ignored_items:
                current_level.setdefault(part, 'IGNORED')
                break
            current_level = current_level.setdefault(part, {})
        else:
            continue
    
    def generate_lines(d, prefix="", current_path=""):
        lines = []
        items = sorted(d.keys())
        
        # Separate items for processing
        dirs = [item for item in items if isinstance(d[item], dict)]
        files = [item for item in items if not isinstance(d[item], dict) and d[item] != 'IGNORED']
        ignored_nodes = [item for item in items if d[item] == 'IGNORED']
        
        all_renderable_items = dirs + files + ignored_nodes
        
        for i, name in enumerate(all_renderable_items):
            connector = "└── " if i == len(all_renderable_items) - 1 else "├── "
            
            if name in ignored_nodes:
                lines.append(f"{prefix}{connector}{name}  [ignored]")
                continue

            if name in dirs:
                lines.append(f"{prefix}{connector}{name}")
                extension = "    " if i == len(all_renderable_items) - 1 else "│   "
                new_path = os.path.join(current_path, name)
                lines.extend(generate_lines(d[name], prefix + extension, new_path))
                continue

            # Process files
            item_full_path_str = os.path.join(base_dir, current_path, name)
            item_normalized_path = os.path.normcase(os.path.abspath(item_full_path_str))
            is_content_included = item_normalized_path in content_set
            
            annotations = []
            if is_annotated_mode:
                if _is_binary_file(item_normalized_path):
                    annotations.append("binary file")
                else:
                    line_count = _get_line_count(item_normalized_path)
                    if line_count > 0:
                        annotations.append(f"{line_count} lines")
                if not is_content_included:
                    annotations.append("content omitted")
            elif is_content_included: # Standard mode, only annotate included files
                if _is_binary_file(item_normalized_path):
                    annotations.append("binary file")
                else:
                    line_count = _get_line_count(item_normalized_path)
                    if line_count > 0:
                        annotations.append(f"{line_count} lines")

            annotation_str = f"  [{' | '.join(annotations)}]" if annotations else ""
            
            if is_annotated_mode or is_content_included:
                 lines.append(f"{prefix}{connector}{name}{annotation_str}")

        # Add summary for omitted files in standard mode
        if not is_annotated_mode:
            omitted_file_count = len(files) - sum(1 for name in files if os.path.normcase(os.path.abspath(os.path.join(base_dir, current_path, name))) in content_set)
            if omitted_file_count > 0:
                plural = "s" if omitted_file_count > 1 else ""
                connector = "└── "
                lines.append(f"{prefix}{connector}[{omitted_file_count} other file{plural} omitted]")

        return lines
    
    root_folder_name = os.path.basename(root_path)
    tree_lines = [root_folder_name]
    tree_lines.extend(generate_lines(tree_dict.get(root_folder_name, {}), "", root_folder_name))
    return "\n".join(tree_lines)


def generate_text_content(root_path, files_for_tree, files_for_content, is_annotated_mode, ignored_items, log_callback, success_callback, final_callback, progress_callback=None):
    """
    Generates the final text output with directory structure and file contents.
    """
    try:
        final_content = []
        base_path_for_relpath = os.path.dirname(root_path)

        log_callback("\n--- Building Directory Tree ---")
        tree_structure = build_annotated_tree(root_path, files_for_tree, files_for_content, is_annotated_mode, ignored_items)
        
        final_content.append("# Codebase Structure and File Contents\n\n")
        final_content.append("## Project Structure\n\n```text\n")
        final_content.append(tree_structure)
        final_content.append("\n```\n\n---\n\n## File Contents\n\n")

        log_callback("\n--- Processing Selected File Contents into Markdown ---")
        for file_path in sorted(files_for_content):
            relative_path = os.path.relpath(file_path, base_path_for_relpath).replace(os.sep, '/')

            try:
                file_size = os.path.getsize(file_path)
                if file_size > MAX_FILE_SIZE_BYTES:
                    raise FileTooLargeError(f"File is larger than {MAX_FILE_SIZE_MB}MB")
                if _is_binary_file(file_path):
                    raise BinaryFileError("File is binary")

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