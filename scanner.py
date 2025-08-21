# scanner.py
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from constants import MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB
from file_processor_utils import FileProcessingError, FileTooLargeError, BinaryFileError, _is_binary_file

def scan_directory(path, ignored_items, cancel_event=None):
    """
    Scans a directory recursively and builds a data structure for the treeview,
    including line counts for files. Can be cancelled.
    """
    if cancel_event and cancel_event.is_set():
        return None

    item_path = os.path.abspath(path)
    item_name = os.path.basename(item_path)
    is_ignored = item_name in ignored_items

    if os.path.isfile(item_path):
        file_node = {
            'path': item_path, 'name': item_name, 'is_dir': False,
            'is_ignored': is_ignored, 'children': [], 'line_count': None, 'error': None
        }
        if not is_ignored:
            try:
                if os.path.getsize(item_path) > MAX_FILE_SIZE_BYTES:
                    raise FileTooLargeError(f"> {MAX_FILE_SIZE_MB}MB")
                if _is_binary_file(item_path):
                    raise BinaryFileError("binary")
                
                with open(item_path, 'r', encoding='utf-8', errors='ignore') as f:
                    file_node['line_count'] = sum(1 for _ in f)
            except (OSError, FileProcessingError) as e:
                file_node['error'] = str(e)
        return file_node

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
            # FIX (Ruff E701): Split statement to its own line
            if cancel_event and cancel_event.is_set():
                return None
            child_node = scan_directory(os.path.join(item_path, name), ignored_items, cancel_event)
            if child_node:
                node['children'].append(child_node)
            # FIX (Ruff E701): Split statement to its own line
            elif cancel_event and cancel_event.is_set():
                return None
    except (PermissionError, FileNotFoundError):
        pass
    return node

def _process_file_for_scan(file_path):
    """Worker function for the thread pool during scanning."""
    details = {'line_count': None, 'error': None, 'content': None}
    try:
        if os.path.getsize(file_path) > MAX_FILE_SIZE_BYTES:
            raise FileTooLargeError(f"> {MAX_FILE_SIZE_MB}MB")
        if _is_binary_file(file_path):
            raise BinaryFileError("binary")
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        details['content'] = content
        details['line_count'] = content.count('\n') + 1

    except (OSError, FileProcessingError) as e:
        details['error'] = str(e)
    
    return file_path, details

def scan_directory_fast(path, ignored_items, cancel_event=None):
    """
    Scans a directory using a thread pool to accelerate file analysis and correctly builds the tree structure,
    including ignored files/folders which are marked accordingly.
    """
    if not os.path.isdir(path):
        return None

    nodes = {}
    file_paths_to_process = []

    # First, build the entire directory and file structure map from a single walk
    for root, dirs, files in os.walk(path, topdown=True):
        if cancel_event and cancel_event.is_set():
            return None

        # Add the directory node for the current root
        norm_root = os.path.normcase(os.path.abspath(root))
        if norm_root not in nodes:
            nodes[norm_root] = {
                'path': root, 'name': os.path.basename(root), 'is_dir': True,
                'is_ignored': os.path.basename(root) in ignored_items, 'children': []
            }

        # Process subdirectories, adding them to our node map
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            norm_path = os.path.normcase(os.path.abspath(dir_path))
            nodes[norm_path] = {
                'path': dir_path, 'name': dir_name, 'is_dir': True,
                'is_ignored': dir_name in ignored_items, 'children': []
            }

        # Process files, adding them to our node map
        for file_name in files:
            file_path = os.path.join(root, file_name)
            norm_path = os.path.normcase(os.path.abspath(file_path))
            is_ignored = file_name in ignored_items
            nodes[norm_path] = {
                'path': file_path, 'name': file_name, 'is_dir': False,
                'is_ignored': is_ignored
            }
            if not is_ignored:
                file_paths_to_process.append(file_path)

        # Prune traversal into ignored directories for performance
        dirs[:] = [d for d in dirs if d not in ignored_items]

    # Process non-ignored files in parallel to get their content and line counts
    with ThreadPoolExecutor() as executor:
        future_to_path = {executor.submit(_process_file_for_scan, fp): fp for fp in file_paths_to_process}
        for future in as_completed(future_to_path):
            if cancel_event and cancel_event.is_set():
                executor.shutdown(wait=False, cancel_futures=True)
                return None
            try:
                file_path, details = future.result()
                norm_path = os.path.normcase(os.path.abspath(file_path))
                if norm_path in nodes:
                    nodes[norm_path].update(details)
            except Exception:
                pass

    # Link children to their parents to build the tree structure
    norm_root_path = os.path.normcase(os.path.abspath(path))
    for norm_path, node in nodes.items():
        if norm_path == norm_root_path:
            continue
        parent_dir = os.path.dirname(node['path'])
        norm_parent_dir = os.path.normcase(os.path.abspath(parent_dir))
        if norm_parent_dir in nodes:
            nodes[norm_parent_dir].setdefault('children', []).append(node)

    # Sort children recursively for consistent display
    def sort_children_recursive(node):
        if 'children' in node and node.get('is_dir'):
            node['children'].sort(key=lambda x: (not x.get('is_dir', False), x.get('name', '').lower()))
            for child in node['children']:
                sort_children_recursive(child)
    
    root_node = nodes.get(norm_root_path)
    if root_node:
        sort_children_recursive(root_node)
    
    return root_node