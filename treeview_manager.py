# treeview_manager.py
import os
import tkinter.font as tkfont
from tkinter import ttk
from constants import CHECKED_EMOJI, UNCHECKED_EMOJI, MAX_FILE_SIZE_MB
from file_processor_utils import BinaryFileError, FileTooLargeError

class TreeViewManager:
    """
    Manages the Treeview widget, including population from a data structure,
    item checking, and event handling.
    """
    def __init__(self, tree_widget, root_window, log_callback, ignored_items):
        self.tree = tree_widget
        self.root = root_window
        self.log_message = log_callback
        self.ignored_items = ignored_items
        self.tree_font = self._get_tree_font()
        self.tree.bind("<Button-1>", self.handle_tree_click)

    def _get_tree_font(self):
        try:
            style = ttk.Style()
            self.root.update_idletasks()
            font_name = style.lookup("Ttreeview", "font")
            return tkfont.Font(font=font_name)
        except Exception:
            return tkfont.Font()

    def clear_tree(self):
        """Removes all items from the treeview."""
        for i in self.tree.get_children():
            self.tree.delete(i)

    def populate_from_data(self, root_node_data):
        """
        Populates the treeview from a pre-scanned dictionary structure.
        This method is fast as it only performs UI operations.
        """
        self.clear_tree()
        if not root_node_data:
            return
        
        # The root node has a special state "root_state" to make it non-toggleable.
        root_node = self.tree.insert("", "end", text=f" {CHECKED_EMOJI} {root_node_data['name']}", open=True, values=[root_node_data['path'], "root_state"])
        if root_node_data.get('children'):
            self._populate_recursive(root_node_data['children'], root_node)

    def _populate_recursive(self, children_data, parent_node):
        for item_data in children_data:
            path = item_data['path']
            name = item_data['name']
            is_ignored = item_data['is_ignored']
            is_dir = item_data['is_dir']

            annotation = ""
            if not is_dir and not is_ignored:
                line_count = item_data.get('line_count')
                error = item_data.get('error')
                if error:
                    annotation = f"  [{error}]"
                elif line_count is not None:
                    annotation = f"  [{line_count} lines]"

            if is_ignored:
                node_text = f" {UNCHECKED_EMOJI} {name}"
                self.tree.insert(parent_node, "end", text=node_text, open=False, values=[path, "ignored"], tags=('ignored',))
            else:
                node_text = f" {CHECKED_EMOJI} {name}{annotation}"
                node = self.tree.insert(parent_node, "end", text=node_text, open=False, values=[path, "checked"])
                if is_dir and item_data.get('children'):
                    self._populate_recursive(item_data['children'], node)

    def handle_tree_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        values = self.tree.item(item_id, "values")
        # Ignored items are not interactive at all.
        if not values or values[1] == "ignored":
            return

        try:
            bbox = self.tree.bbox(item_id, "text")
        except Exception:
            return
        if not bbox:
            return
            
        item_text = self.tree.item(item_id, "text")
        main_text, _, annotation = item_text.partition('  [')
        
        checkbox_area_text = f" {CHECKED_EMOJI} "
        checkbox_width = self.tree_font.measure(checkbox_area_text)
        text_width = self.tree_font.measure(main_text)

        if bbox[0] <= event.x < bbox[0] + checkbox_width:
            # Prevent toggling the state of the root item.
            if values[1] != "root_state":
                self.toggle_check_state(item_id)
        elif bbox[0] + checkbox_width <= event.x < bbox[0] + text_width:
            if os.path.isdir(values[0]):
                self.tree.item(item_id, open=not self.tree.item(item_id, "open"))

    def toggle_check_state(self, item_id):
        values = self.tree.item(item_id, "values")
        if not values or values[1] in ["ignored", "root_state"]:
            return
        new_state = "unchecked" if values[1] == "checked" else "checked"
        self.update_check_state(item_id, new_state)

    def update_check_state(self, item_id, state):
        values = self.tree.item(item_id, "values")
        # Prevent changing the state of ignored items or the special root item.
        if not values or values[1] in ["ignored", "root_state"]:
            return

        current_text = self.tree.item(item_id, "text")
        base_text, _, annotation_part = current_text.partition('  [')
        
        text_parts = base_text.strip().split(' ', 1)
        item_name = text_parts[1] if len(text_parts) > 1 else ""
        
        emoji = CHECKED_EMOJI if state == "checked" else UNCHECKED_EMOJI
        new_text = f" {emoji} {item_name}"
        
        if annotation_part:
            new_text += f"  [{annotation_part}"

        self.tree.item(item_id, text=new_text, values=[values[0], state])
        for child_id in self.tree.get_children(item_id):
            self.update_check_state(child_id, state)

    def get_checked_files(self):
        checked_files = []
        def _recurse_tree(item_id):
            values = self.tree.item(item_id, "values")
            if not values:
                return
            path, state = values[0], values[1]

            # We traverse into children if the node is checked OR it's the special root node.
            if state == "checked" or state == "root_state":
                # Only add the path if it's a file and is explicitly checked (not the root).
                if os.path.isfile(path) and state == "checked":
                    checked_files.append(path)
                
                # Recurse into children of any checked directory or the root.
                if os.path.isdir(path):
                    for child_id in self.tree.get_children(item_id):
                        _recurse_tree(child_id)

        root_items = self.tree.get_children()
        if root_items:
            for item in root_items:
                _recurse_tree(item)
        return checked_files

    def get_all_item_states(self):
        states = {}
        def _recurse(item_id):
            values = self.tree.item(item_id, "values")
            if not values:
                return
            
            path, state = values[0], values[1]
            norm_path = os.path.normcase(os.path.abspath(path))
            states[norm_path] = state
            
            for child_id in self.tree.get_children(item_id):
                _recurse(child_id)

        root_items = self.tree.get_children()
        if root_items:
            for item in root_items:
                _recurse(item)
        return states

    def update_tree_with_details(self, file_details_map):
        """
        Recursively updates the treeview items with details like line count or errors.
        This is now mostly redundant as details are shown on scan, but can be used for updates.
        """
        def _recurse_update(item_id):
            values = self.tree.item(item_id, "values")
            if not values:
                return

            path, state = values[0], values[1]
            if state != "ignored" and os.path.isfile(path):
                norm_path = os.path.normcase(os.path.abspath(path))
                details = file_details_map.get(norm_path)

                if details:
                    current_text = self.tree.item(item_id, "text")
                    base_text, _, _ = current_text.partition('  [')
                    
                    annotation = ""
                    error = details.get('error')
                    if error:
                        if isinstance(error, BinaryFileError):
                            annotation = "binary file"
                        elif isinstance(error, FileTooLargeError):
                            annotation = f"file > {MAX_FILE_SIZE_MB}MB"
                        else:
                            annotation = "read error"
                    elif 'line_count' in details:
                        annotation = f"{details['line_count']} lines"

                    if annotation:
                        new_text = f"{base_text.strip()}  [{annotation}]"
                        self.tree.item(item_id, text=new_text)

            for child_id in self.tree.get_children(item_id):
                _recurse_update(child_id)

        root_items = self.tree.get_children()
        if root_items:
            for item in root_items:
                _recurse_update(item)

    def check_all(self):
        for item_id in self.tree.get_children():
            # This will start the recursion on the root, but the guard in
            # update_check_state will prevent the root itself from changing.
            # It will, however, correctly check all of its children.
            self.update_check_state(item_id, "checked")

    def uncheck_all(self):
        for item_id in self.tree.get_children():
            # Same logic as check_all applies here.
            self.update_check_state(item_id, "unchecked")

    def check_selected(self):
        for item_id in self.tree.selection():
            self.update_check_state(item_id, "checked")

    def uncheck_selected(self):
        for item_id in self.tree.selection():
            self.update_check_state(item_id, "unchecked")