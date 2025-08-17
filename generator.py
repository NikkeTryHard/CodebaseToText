# generator.py
import os
import time
import traceback
from file_processor_utils import get_language_identifier

def _flatten_tree_to_map(node):
    """
    Iteratively flattens the scanned tree data into a dictionary
    mapping a normalized path to its node data for fast lookups.
    """
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
    Performs a single iterative pass to mark which nodes should be visible in Standard Mode.
    A node is visible if it's checked, or if any of its descendants are checked.
    """
    stack = [(node, False)]  # (current_node, is_processed)
    
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
        
        stack[-1] = (current, True)  # Mark as processed for the next iteration
        
        if current.get('is_dir') and 'children' in current:
            for child in reversed(current['children']):
                stack.append((child, False))
    
    return node['_is_visible']

def _generate_tree_lines_from_node(node, is_annotated_mode, prefix=""):
    """
    Iteratively traverses the pre-scanned tree data structure to generate
    the visual tree representation. This is extremely fast as visibility is pre-calculated.
    """
    lines = []
    stack = []  # We'll use a list to simulate the stack: (child_index, children, cur_prefix, current_node)
    
    children = node.get('children', [])
    child_index = len(children) - 1
    stack.append((child_index, children, prefix, node))
    
    while stack:
        child_index, children, cur_prefix, current = stack[-1]
        
        if child_index < 0:
            stack.pop()
            continue
        
        child = children[child_index]
        stack[-1] = (child_index - 1, children, cur_prefix, current)  # Decrement index for next iteration
        
        if not is_annotated_mode and not child.get('_is_visible'):
            continue
        
        is_last = (child_index == len(children) - 1)
        connector = "└── " if is_last else "├── "
        extension = "    " if is_last else "│   "
        
        name = child['name']
        annotations = []
        
        if child.get('is_dir'):
            lines.append(f"{cur_prefix}{connector}{name}")
            
            child_children = child.get('children', [])
            child_child_index = len(child_children) - 1
            stack.append((child_child_index, child_children, cur_prefix + extension, child))
        else:
            error = child.get('error')
            if error:
                annotations.append(str(error))
            elif child.get('line_count') is not None:
                annotations.append(f"{child['line_count']} lines")
            
            if is_annotated_mode and not child.get('_is_visible') and not error:
                annotations.append("content omitted")
            
            annotation_str = f"  [{' | '.join(annotations)}]" if annotations else ""
            lines.append(f"{cur_prefix}{connector}{name}{annotation_str}")
    
    return lines

def generate_text_content_fast(root_path, scanned_tree_data, files_for_content, is_annotated_mode, log_callback, success_callback, final_callback, cancel_event=None, status_callback=None, progress_callback=None):
    """
    Generates the final text output by traversing the pre-scanned data.
    This function is now almost instantaneous.
    """
    def update_status(msg):
        if status_callback:
            status_callback(msg)

    try:
        final_content = []
        base_path_for_relpath = os.path.dirname(root_path)

        # 1. Pre-calculation Step (very fast single pass)
        update_status("Analyzing selections...")
        if cancel_event and cancel_event.is_set():
            return
        content_set = {os.path.normcase(os.path.abspath(p)) for p in files_for_content}
        _mark_visible_nodes(scanned_tree_data, content_set)

        # 2. Build the Project Structure tree string (now lightning fast)
        update_status("Building directory tree...")
        if cancel_event and cancel_event.is_set():
            return
        
        tree_header = f"{scanned_tree_data['name']}"
        tree_lines = _generate_tree_lines_from_node(scanned_tree_data, is_annotated_mode)
        tree_structure = "\n".join([tree_header] + tree_lines)

        final_content.append("# Codebase Structure and File Contents\n\n## Project Structure\n\n```text\n")
        final_content.append(tree_structure)
        final_content.append("\n```\n\n---\n\n## File Contents\n\n")

        # 3. Flatten the tree for instant file content lookups
        update_status("Preparing file content...")
        if cancel_event and cancel_event.is_set():
            return
        file_details_map = _flatten_tree_to_map(scanned_tree_data)

        # 4. Append file contents (very fast)
        update_status("Formatting final output...")
        content_files = files_for_content  # No sorting needed; already in tree order
        total_files = len(content_files)
        last_progress_update = time.time()

        for i, file_path in enumerate(content_files):
            if cancel_event and cancel_event.is_set():
                return
            
            norm_path = os.path.normcase(os.path.abspath(file_path))
            details = file_details_map.get(norm_path)

            if details and not details.get('error') and details.get('content') is not None:
                relative_path = os.path.relpath(file_path, base_path_for_relpath).replace(os.sep, '/')
                final_content.append(f"### `{relative_path}`\n\n")
                
                language = get_language_identifier(file_path)
                final_content.append(f"```{language}\n{details['content']}\n```\n\n---\n\n")
            
            # Batch progress updates to avoid overwhelming the UI event loop
            if progress_callback and time.time() - last_progress_update > 0.1:
                progress_callback(i + 1, total_files)
                last_progress_update = time.time()

        if progress_callback:
            progress_callback(total_files, total_files)  # Ensure final progress is 100%

        if not (cancel_event and cancel_event.is_set()):
            success_callback("".join(final_content))

    except Exception as e:
        update_status("An unexpected error occurred.")
        log_callback(f"An unexpected error occurred during generation: {e}\nTraceback:\n{traceback.format_exc()}")
    finally:
        if final_callback:
            final_callback()