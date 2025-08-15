# file_processor.py
import os
import traceback
from constants import LANGUAGE_MAP, MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB

# --- Custom Exceptions ---
class FileProcessingError(Exception):
    """Base class for file processing errors."""
    pass

class FileTooLargeError(FileProcessingError):
    """Raised when a file is too large to process."""
    pass

class BinaryFileError(FileProcessingError):
    """Raised when a file is identified as binary."""
    pass

# --- Helper Functions ---
def get_all_files(directory):
    """Recursively gets all file paths in a directory."""
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

def get_language_identifier(file_path):
    """Gets the language identifier for a file path."""
    filename = os.path.basename(file_path)
    _, ext = os.path.splitext(filename)
    if filename.lower() in LANGUAGE_MAP:
        return LANGUAGE_MAP[filename.lower()]
    if ext.lower() in LANGUAGE_MAP:
        return LANGUAGE_MAP[ext.lower()]
    return 'text'

def scan_directory(path, ignored_items):
    """
    Scans a directory recursively and builds a data structure for the treeview.
    """
    item_path = os.path.abspath(path)
    item_name = os.path.basename(item_path)
    is_ignored = item_name in ignored_items

    if os.path.isfile(item_path):
        return {
            'path': item_path, 'name': item_name, 'is_dir': False,
            'is_ignored': is_ignored, 'children': []
        }

    if is_ignored:
        return {
            'path': item_path, 'name': item_name, 'is_dir': True,
            'is_ignored': True, 'children': []
        }

    node = {
        'path': item_path, 'name': item_name, 'is_dir': True,
        'is_ignored': False, 'children': []
    }
    try:
        items = sorted(os.listdir(item_path), key=lambda x: (not os.path.isdir(os.path.join(item_path, x)), x.lower()))
        for name in items:
            child_node = scan_directory(os.path.join(item_path, name), ignored_items)
            if child_node:
                node['children'].append(child_node)
    except (PermissionError, FileNotFoundError):
        pass
    return node

# --- Tree Building Function (for Generation Phase) ---
def build_annotated_tree(root_path, files_for_tree, files_for_content, is_annotated_mode, ignored_items, item_states, file_details_map):
    """
    Builds a string representation of the directory tree using pre-processed file details.
    This function does NOT perform any file I/O.
    """
    tree_dict = {}
    base_dir = os.path.dirname(root_path)
    content_set = {os.path.normcase(os.path.abspath(p)) for p in files_for_content}

    for path in files_for_tree:
        try:
            relative_path = os.path.relpath(path, base_dir).replace(os.sep, '/')
        except ValueError:
            continue
            
        parts = relative_path.split('/')
        current_level = tree_dict
        full_path_parts = []
        
        for part in parts:
            full_path_parts.append(part)
            current_part_path = os.path.normcase(os.path.abspath(os.path.join(base_dir, *full_path_parts)))
            
            # Stop descending if we hit a node that's already been marked
            if isinstance(current_level.get(part), str):
                current_level = None # Invalidate current_level to stop processing this path
                break

            if part in ignored_items:
                current_level[part] = 'IGNORED'
                current_level = None
                break
            
            if not is_annotated_mode and item_states.get(current_part_path) == 'unchecked':
                current_level[part] = 'UNCHECKED_DIR'
                current_level = None
                break
            
            current_level = current_level.setdefault(part, {})
        
        if current_level is None:
            continue

    def generate_lines(d, prefix="", current_path=""):
        lines = []
        items = sorted(d.keys())
        
        dirs = [item for item in items if isinstance(d[item], dict)]
        all_files = [item for item in items if not isinstance(d[item], dict) and d[item] not in ['IGNORED', 'UNCHECKED_DIR']]
        ignored_nodes = [item for item in items if d[item] == 'IGNORED']
        unchecked_dirs = [item for item in items if d[item] == 'UNCHECKED_DIR']

        files_to_render = []
        omitted_summary_item = None

        if is_annotated_mode:
            files_to_render = all_files
        else:
            included_files = [name for name in all_files if os.path.normcase(os.path.abspath(os.path.join(base_dir, current_path, name))) in content_set]
            files_to_render = included_files
            omitted_file_count = len(all_files) - len(files_to_render)
            if omitted_file_count > 0:
                plural = "s" if omitted_file_count > 1 else ""
                omitted_summary_item = f"[{omitted_file_count} other file{plural} omitted]"

        all_renderable_items = dirs + unchecked_dirs + files_to_render + ignored_nodes
        if omitted_summary_item:
            all_renderable_items.append(omitted_summary_item)

        for i, name in enumerate(all_renderable_items):
            connector = "└── " if i == len(all_renderable_items) - 1 else "├── "
            extension = "    " if i == len(all_renderable_items) - 1 else "│   "
            
            if name == omitted_summary_item:
                lines.append(f"{prefix}{connector}{name}")
                continue

            if name in ignored_nodes:
                lines.append(f"{prefix}{connector}{name}  [ignored]")
                continue
                
            if name in unchecked_dirs:
                lines.append(f"{prefix}{connector}{name}  [content omitted]")
                continue

            if name in dirs:
                lines.append(f"{prefix}{connector}{name}")
                new_path = os.path.join(current_path, name)
                lines.extend(generate_lines(d[name], prefix + extension, new_path))
                continue

            item_full_path_str = os.path.join(base_dir, current_path, name)
            item_normalized_path = os.path.normcase(os.path.abspath(item_full_path_str))
            is_content_included = item_normalized_path in content_set
            
            annotations = []
            details = file_details_map.get(item_normalized_path)

            has_error = details and details.get('error')
            if has_error:
                annotations.append(str(details['error']))
            
            if is_content_included and details and 'line_count' in details:
                annotations.append(f"{details['line_count']} lines")
            
            if is_annotated_mode and not is_content_included and not has_error:
                annotations.append("content omitted")

            annotation_str = f"  [{' | '.join(annotations)}]" if annotations else ""
            lines.append(f"{prefix}{connector}{name}{annotation_str}")

        return lines
    
    root_folder_name = os.path.basename(root_path)
    tree_lines = [root_folder_name]
    tree_lines.extend(generate_lines(tree_dict.get(root_folder_name, {}), "", root_folder_name))
    return "\n".join(tree_lines)


# --- Main Generation Function (Optimized) ---
def generate_text_content(root_path, files_for_tree, files_for_content, is_annotated_mode, ignored_items, item_states, log_callback, success_callback, final_callback, progress_callback=None, status_callback=None):
    """
    Generates the final text output. Optimized to read each file only once.
    """
    def update_status(msg):
        if status_callback:
            status_callback(msg)

    try:
        final_content = []
        base_path_for_relpath = os.path.dirname(root_path)
        
        total_files = len(files_for_content)
        update_status(f"Analyzing {total_files} selected files...")
        log_callback("\n--- Reading and analyzing selected files ---")
        processed_files = []
        
        for i, file_path in enumerate(sorted(files_for_content)):
            update_status(f"Reading file {i+1}/{total_files}: {os.path.basename(file_path)}")
            details = {'path': file_path, 'content': None, 'error': None}
            try:
                if os.path.getsize(file_path) > MAX_FILE_SIZE_BYTES:
                    raise FileTooLargeError(f"File > {MAX_FILE_SIZE_MB}MB")
                if _is_binary_file(file_path):
                    raise BinaryFileError("Binary file")

                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                details['content'] = content
                details['line_count'] = content.count('\n') + 1

            except (OSError, FileProcessingError) as e:
                details['error'] = e
            
            processed_files.append(details)
            if progress_callback:
                progress_callback()
        
        file_details_map = {os.path.normcase(os.path.abspath(f['path'])): f for f in processed_files}

        update_status("Building directory tree...")
        log_callback("\n--- Building Directory Tree ---")
        tree_structure = build_annotated_tree(root_path, files_for_tree, files_for_content, is_annotated_mode, ignored_items, item_states, file_details_map)
        
        final_content.append("# Codebase Structure and File Contents\n\n")
        final_content.append("## Project Structure\n\n```text\n")
        final_content.append(tree_structure)
        final_content.append("\n```\n\n---\n\n## File Contents\n\n")

        update_status("Formatting final output...")
        log_callback("\n--- Formatting final output ---")
        for details in processed_files:
            relative_path = os.path.relpath(details['path'], base_path_for_relpath).replace(os.sep, '/')
            final_content.append(f"### `{relative_path}`\n\n")
            
            if details['error']:
                final_content.append(f"```text\n--- CONTENT SKIPPED: {details['error']} ---\n```\n\n")
            else:
                language = get_language_identifier(details['path'])
                final_content.append(f"```{language}\n")
                final_content.append(details['content'])
                final_content.append("\n```\n\n")
            
            final_content.append("---\n\n")
        
        update_status("Generation complete!")
        success_callback("".join(final_content))

    except Exception as e:
        update_status("An unexpected error occurred.")
        log_callback(f"An unexpected error occurred during generation: {e}")
        log_callback(f"Traceback:\n{traceback.format_exc()}")
    finally:
        final_callback()