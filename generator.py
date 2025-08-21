# generator.py
import os
import time
import traceback
from file_processor_utils import get_language_identifier

def _flatten_tree_to_map(node):
    """Flattens the scanned tree data into a dictionary for fast lookups."""
    node_map = {}
    stack = [node]
    while stack:
        current = stack.pop()
        norm_path = os.path.normcase(os.path.abspath(current['path']))
        node_map[norm_path] = current
        if current.get('is_dir') and 'children' in current:
            stack.extend(current['children'])
    return node_map

def _mark_visible_nodes(node, content_set):
    """
    Marks nodes as visible if they are checked or have a checked descendant.
    This is the crucial pre-processing step for the generator.
    """
    stack = [(node, False)]
    while stack:
        current, is_processed = stack[-1]
        if is_processed:
            stack.pop()
            norm_path = os.path.normcase(os.path.abspath(current['path']))
            is_checked = norm_path in content_set
            if current.get('is_dir') and 'children' in current:
                child_is_visible = any(child.get('_is_visible', False) for child in current['children'])
                current['_is_visible'] = is_checked or child_is_visible
            else:
                current['_is_visible'] = is_checked
            continue
        stack[-1] = (current, True)
        if current.get('is_dir') and 'children' in current:
            for child in reversed(current['children']):
                stack.append((child, False))
    return node.get('_is_visible', False)

def _generate_tree_lines_recursive(node, is_annotated_mode, prefix=""):
    """
    Correctly and recursively traverses the tree data to generate the visual tree
    for the output file, handling all states: ignored, omitted, and visible.
    """
    lines = []
    children = node.get('children', [])
    
    for i, child in enumerate(children):
        is_last = (i == len(children) - 1)
        connector = "└── " if is_last else "├── "
        extension = "    " if is_last else "│   "
        
        is_visible = child.get('_is_visible', False)
        
        # --- Determine if this node should be shown at all ---
        should_show_node = (
            child.get('is_ignored') or 
            is_annotated_mode or 
            (not is_annotated_mode and is_visible)
        )

        if not should_show_node:
            continue

        # --- Build the output line for the node ---
        annotations = []
        
        # 1. Highest priority: Ignored
        if child.get('is_ignored'):
            annotations.append("ignored")
        # 2. Annotated Mode: Handle omitted items
        elif is_annotated_mode and not is_visible:
            if child.get('is_dir'):
                annotations.append("omitted")
            else: # It's a file
                if child.get('error'):
                    annotations.append(str(child['error']))
                elif child.get('line_count') is not None:
                    annotations.append(f"{child['line_count']} lines")
                annotations.append("content omitted")
        # 3. Visible items (in either mode)
        else:
            if not child.get('is_dir'):
                if child.get('error'):
                    annotations.append(str(child['error']))
                elif child.get('line_count') is not None:
                    annotations.append(f"{child['line_count']} lines")

        annotation_str = f"  [{' | '.join(annotations)}]" if annotations else ""
        lines.append(f"{prefix}{connector}{child['name']}{annotation_str}")

        # --- Decide whether to recurse into children ---
        should_recurse = (
            child.get('is_dir') and
            not child.get('is_ignored') and
            not (is_annotated_mode and not is_visible) # Don't recurse into omitted folders
        )

        if should_recurse:
            lines.extend(_generate_tree_lines_recursive(child, is_annotated_mode, prefix + extension))
            
    return lines

def generate_text_content_fast(root_path, scanned_tree_data, files_for_content, is_annotated_mode, log_callback, success_callback, final_callback, cancel_event=None, status_callback=None, progress_callback=None):
    def update_status(msg):
        if status_callback: status_callback(msg)

    try:
        final_content = []
        base_path_for_relpath = os.path.dirname(root_path)

        update_status("Analyzing selections...")
        if cancel_event and cancel_event.is_set(): return
        content_set = {os.path.normcase(os.path.abspath(p)) for p in files_for_content}
        _mark_visible_nodes(scanned_tree_data, content_set)

        update_status("Building directory tree...")
        if cancel_event and cancel_event.is_set(): return
        
        tree_header = f"{scanned_tree_data['name']}"
        tree_lines = _generate_tree_lines_recursive(scanned_tree_data, is_annotated_mode)
        tree_structure = "\n".join([tree_header] + tree_lines)

        final_content.append("# Codebase Structure and File Contents\n\n## Project Structure\n\n```text\n")
        final_content.append(tree_structure)
        final_content.append("\n```\n\n---\n\n## File Contents\n\n")

        update_status("Preparing file content...")
        if cancel_event and cancel_event.is_set(): return
        file_details_map = _flatten_tree_to_map(scanned_tree_data)

        update_status("Formatting final output...")
        total_files = len(files_for_content)
        last_progress_update = time.time()

        for i, file_path in enumerate(files_for_content):
            if cancel_event and cancel_event.is_set(): return
            
            norm_path = os.path.normcase(os.path.abspath(file_path))
            details = file_details_map.get(norm_path)

            if details and not details.get('error') and details.get('content') is not None:
                relative_path = os.path.relpath(file_path, base_path_for_relpath).replace(os.sep, '/')
                final_content.append(f"### `{relative_path}`\n\n")
                
                language = get_language_identifier(file_path)
                final_content.append(f"```{language}\n{details['content']}\n```\n\n---\n\n")
            
            if progress_callback and time.time() - last_progress_update > 0.1:
                progress_callback(i + 1, total_files)
                last_progress_update = time.time()

        if progress_callback:
            progress_callback(total_files, total_files)

        if not (cancel_event and cancel_event.is_set()):
            success_callback("".join(final_content))

    except Exception as e:
        update_status("An unexpected error occurred.")
        log_callback(f"An unexpected error occurred during generation: {e}\nTraceback:\n{traceback.format_exc()}")
    finally:
        if final_callback:
            final_callback()