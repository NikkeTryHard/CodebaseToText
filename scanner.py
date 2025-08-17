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

def _process_file_for_scan(file_path, cache):
    """Worker function for the thread pool during scanning."""
    cached_details = cache.get(file_path)
    if cached_details:
        return file_path, cached_details

    details = {'line_count': None, 'error': None}
    try:
        if os.path.getsize(file_path) > MAX_FILE_SIZE_BYTES:
            raise FileTooLargeError(f"> {MAX_FILE_SIZE_MB}MB")
        if _is_binary_file(file_path):
            raise BinaryFileError("binary")
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            details['line_count'] = sum(1 for _ in f)
    except (OSError, FileProcessingError) as e:
        details['error'] = str(e)
    
    cache.set(file_path, details)
    return file_path, details

def scan_directory_fast(path, ignored_items, cache, cancel_event=None):
    """
    Scans a directory using a thread pool to accelerate file analysis and correctly builds the tree structure.
    """
    # FIX (Ruff E701): Split statement to its own line
    if not os.path.isdir(path):
        return None

    file_paths_to_process = []
    nodes = {}

    for root, dirs, files in os.walk(path, topdown=True):
        # FIX (Ruff E701): Split statement to its own line
        if cancel_event and cancel_event.is_set():
            return None
        dirs[:] = [d for d in dirs if d not in ignored_items]
        
        for file_name in files:
            if file_name not in ignored_items:
                file_paths_to_process.append(os.path.join(root, file_name))

    with ThreadPoolExecutor() as executor:
        future_to_path = {executor.submit(_process_file_for_scan, fp, cache): fp for fp in file_paths_to_process}
        for future in as_completed(future_to_path):
            if cancel_event and cancel_event.is_set():
                executor.shutdown(wait=False, cancel_futures=True)
                return None
            try:
                file_path, details = future.result()
                norm_path = os.path.normcase(os.path.abspath(file_path))
                nodes[norm_path] = {
                    'path': file_path, 'name': os.path.basename(file_path), 'is_dir': False,
                    'is_ignored': os.path.basename(file_path) in ignored_items, **details
                }
            except Exception:
                pass

    for root, dirs, _ in os.walk(path, topdown=True):
        dirs[:] = [d for d in dirs if d not in ignored_items]
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            norm_path = os.path.normcase(os.path.abspath(dir_path))
            if norm_path not in nodes:
                nodes[norm_path] = {
                    'path': dir_path, 'name': dir_name, 'is_dir': True,
                    'is_ignored': dir_name in ignored_items, 'children': []
                }

    norm_root_path = os.path.normcase(os.path.abspath(path))
    if norm_root_path not in nodes:
        nodes[norm_root_path] = {
            'path': path, 'name': os.path.basename(path), 'is_dir': True,
            'is_ignored': os.path.basename(path) in ignored_items, 'children': []
        }

    for norm_path, node in nodes.items():
        parent_dir = os.path.dirname(node['path'])
        norm_parent_dir = os.path.normcase(os.path.abspath(parent_dir))
        if norm_parent_dir in nodes and norm_parent_dir != norm_path:
            nodes[norm_parent_dir].setdefault('children', []).append(node)

    def sort_children_recursive(node):
        if 'children' in node and node.get('is_dir'):
            node['children'].sort(key=lambda x: (not x.get('is_dir', False), x.get('name', '').lower()))
            for child in node['children']:
                sort_children_recursive(child)
    
    root_node = nodes.get(norm_root_path)
    if root_node:
        sort_children_recursive(root_node)
    
    return root_node