# generator.py
import os
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from file_processor_utils import get_language_identifier

def build_annotated_tree(root_path, files_for_tree, files_for_content, is_annotated_mode, ignored_items, item_states, file_details_map):
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
            
            if isinstance(current_level.get(part), str):
                current_level = None
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

            item_full_path_str = os.path.join(base_dir, current_path, name)
            item_normalized_path = os.path.normcase(os.path.abspath(item_full_path_str))
            
            if name in dirs:
                details = file_details_map.get(item_normalized_path)
                line_count_annotation = ""
                if details and 'line_count' in details and details['line_count'] is not None:
                    line_count_annotation = f"  [{details['line_count']} lines]"

                lines.append(f"{prefix}{connector}{name}{line_count_annotation}")
                new_path = os.path.join(current_path, name)
                lines.extend(generate_lines(d[name], prefix + extension, new_path))
                continue

            is_content_included = item_normalized_path in content_set
            annotations = []
            details = file_details_map.get(item_normalized_path)

            if details:
                error = details.get('error')
                if error:
                    annotations.append(str(error))
                elif 'line_count' in details and details['line_count'] is not None and (is_content_included or is_annotated_mode):
                    annotations.append(f"{details['line_count']} lines")
            
            if is_annotated_mode and not is_content_included and not (details and details.get('error')):
                annotations.append("content omitted")

            annotation_str = f"  [{' | '.join(annotations)}]" if annotations else ""
            lines.append(f"{prefix}{connector}{name}{annotation_str}")

        return lines
    
    root_folder_name = os.path.basename(root_path)
    tree_lines = [f"{root_folder_name}"]
    tree_lines.extend(generate_lines(tree_dict.get(root_folder_name, {}), "", root_folder_name))
    return "\n".join(tree_lines)

def _read_file_content_worker(file_path, cache):
    """Worker function to read file content, used for cache misses."""
    details = {}
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        details['content'] = content
        details['line_count'] = content.count('\n') + 1 
        details['error'] = None
    except OSError as e:
        details['content'] = None
        details['error'] = str(e)

    # Set the result in the cache for this session
    cache.set(file_path, details)
    return file_path, details

def generate_text_content_fast(root_path, files_for_tree, files_for_content, is_annotated_mode, ignored_items, item_states, log_callback, success_callback, final_callback, cache, progress_callback=None, status_callback=None, cancel_event=None):
    """
    Generates the final text output. Reads files from disk only if they
    were not pre-loaded into the cache during the scan phase.
    """
    def update_status(msg):
        if status_callback:
            status_callback(msg)

    try:
        final_content = []
        base_path_for_relpath = os.path.dirname(root_path)
        
        file_details_map = {}
        # Populate details from cache for all tree files initially
        for file_path in files_for_tree:
            if os.path.isfile(file_path):
                norm_path = os.path.normcase(os.path.abspath(file_path))
                file_details_map[norm_path] = cache.get(file_path) or {'path': file_path}

        # Identify which files for content are missing from the cache (i.e., content needs to be read)
        files_to_read = [
            fp for fp in files_for_content
            if 'content' not in file_details_map.get(os.path.normcase(os.path.abspath(fp)), {})
        ]

        if files_to_read:
            total_to_read = len(files_to_read)
            update_status(f"Reading content for {total_to_read} files...")
            log_callback(f"\n--- Reading content for {total_to_read} files (cache miss) ---")

            with ThreadPoolExecutor() as executor:
                future_to_path = {executor.submit(_read_file_content_worker, fp, cache): fp for fp in files_to_read}
                for i, future in enumerate(as_completed(future_to_path)):
                    if cancel_event and cancel_event.is_set():
                        executor.shutdown(wait=False, cancel_futures=True)
                        log_callback("Generation cancelled during content reading.")
                        update_status("Cancelled.")
                        return
                    
                    try:
                        file_path, details = future.result()
                        norm_path = os.path.normcase(os.path.abspath(file_path))
                        file_details_map[norm_path] = details
                    except Exception as e:
                        log_callback(f"  - Error reading file in worker: {e}")
                    
                    if progress_callback:
                        progress_callback(i + 1, total_to_read)
        
        if cancel_event and cancel_event.is_set(): return

        update_status("Building directory tree...")
        log_callback("\n--- Building Directory Tree ---")
        tree_structure = build_annotated_tree(root_path, files_for_tree, files_for_content, is_annotated_mode, ignored_items, item_states, file_details_map)
        
        final_content.append("# Codebase Structure and File Contents\n\n## Project Structure\n\n```text\n")
        final_content.append(tree_structure)
        final_content.append("\n```\n\n---\n\n## File Contents\n\n")

        if cancel_event and cancel_event.is_set(): return

        update_status("Formatting final output...")
        log_callback("\n--- Formatting final output ---")
        for file_path in sorted(files_for_content):
            if cancel_event and cancel_event.is_set(): return

            norm_path = os.path.normcase(os.path.abspath(file_path))
            details = file_details_map.get(norm_path)
            if details and not details.get('error') and details.get('content') is not None:
                relative_path = os.path.relpath(details.get('path', file_path), base_path_for_relpath).replace(os.sep, '/')
                final_content.append(f"### `{relative_path}`\n\n")
                
                language = get_language_identifier(details.get('path', file_path))
                final_content.append(f"```{language}\n{details['content']}\n```\n\n---\n\n")

        if not (cancel_event and cancel_event.is_set()):
            success_callback("".join(final_content), file_details_map)

    except Exception as e:
        update_status("An unexpected error occurred.")
        log_callback(f"An unexpected error occurred during generation: {e}\nTraceback:\n{traceback.format_exc()}")
    finally:
        if final_callback:
            final_callback()