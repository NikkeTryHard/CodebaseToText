# treeview_manager.py
import os
from tkinter import PhotoImage

class TreeViewManager:
    """
    Manages the Treeview widget, including population from a data structure,
    item checking, and event handling using robust image-based checkboxes.
    """
    def __init__(self, tree_widget, root_window, log_callback, ignored_items, resource_path_func):
        self.tree = tree_widget
        self.root = root_window
        self.log_message = log_callback
        self.ignored_items = ignored_items
        self.resource_path = resource_path_func

        try:
            self.checked_img = PhotoImage(file=self.resource_path("assets/checked.png"))
            self.unchecked_img = PhotoImage(file=self.resource_path("assets/unchecked.png"))
            self.ignored_img = PhotoImage(file=self.resource_path("assets/unchecked.png"))
        except Exception as e:
            self.log_message(f"Error loading checkbox images: {e}")
            self.checked_img = self.unchecked_img = self.ignored_img = None

        self.tree.bind("<Button-1>", self.handle_tree_click)
        self.tree.bind("<space>", self.handle_spacebar_press)

    def clear_tree(self):
        """Removes all items from the treeview."""
        for i in self.tree.get_children():
            self.tree.delete(i)

    def populate_from_data(self, root_node_data):
        """Populates the treeview using a pre-scanned dictionary structure."""
        self.clear_tree()
        if not root_node_data:
            return
        
        self.tree.insert("", "end", text=f" {root_node_data['name']}", open=True, 
                         image=self.checked_img, values=[root_node_data['path'], "root_state"])
        if root_node_data.get('children'):
            self._populate_recursive(root_node_data['children'], "")

    def _populate_recursive(self, children_data, parent_node):
        for item_data in children_data:
            annotation = ""
            if not item_data['is_dir'] and not item_data['is_ignored']:
                error = item_data.get('error')
                if error:
                    annotation = f"  [{error}]"
                elif item_data.get('line_count') is not None:
                    annotation = f"  [{item_data['line_count']} lines]"

            node_text = f" {item_data['name']}{annotation}"
            
            if item_data['is_ignored']:
                self.tree.insert(parent_node, "end", text=node_text, open=False, 
                                 image=self.ignored_img, values=[item_data['path'], "ignored"], tags=('ignored',))
            else:
                node = self.tree.insert(parent_node, "end", text=node_text, open=False, 
                                        image=self.checked_img, values=[item_data['path'], "checked"])
                if item_data.get('children'):
                    self._populate_recursive(item_data['children'], node)

    def handle_tree_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id: return
        element = self.tree.identify_element(event.x, event.y)
        if "image" in element:
            self.toggle_check_state(item_id)
            return "break"
        elif "text" in element:
            values = self.tree.item(item_id, "values")
            if values and os.path.isdir(values[0]):
                self.tree.item(item_id, open=not self.tree.item(item_id, "open"))
                return "break"

    def handle_spacebar_press(self, event):
        for item_id in self.tree.selection():
            self.toggle_check_state(item_id)
        return "break"

    def toggle_check_state(self, item_id):
        values = self.tree.item(item_id, "values")
        if not values or values[1] in ["ignored", "root_state"]: return
        new_state = "unchecked" if values[1] == "checked" else "checked"
        self.update_check_state(item_id, new_state)

    def update_check_state(self, item_id, state):
        values = self.tree.item(item_id, "values")
        if not values or values[1] in ["ignored", "root_state"]: return

        new_image = self.checked_img if state == "checked" else self.unchecked_img
        self.tree.item(item_id, image=new_image, values=[values[0], state])
        
        for child_id in self.tree.get_children(item_id):
            self.update_check_state(child_id, state)

    def get_checked_files(self):
        checked_files = []
        def _recurse(item_id):
            values = self.tree.item(item_id, "values")
            if not values: return
            path, state = values[0], values[1]
            if state == "checked" or state == "root_state":
                if os.path.isfile(path) and state == "checked":
                    checked_files.append(path)
                if os.path.isdir(path):
                    for child in self.tree.get_children(item_id):
                        _recurse(child)
        for item in self.tree.get_children():
            _recurse(item)
        return checked_files

    def check_all(self):
        root_items = self.tree.get_children()
        if not root_items: return
        for child_id in self.tree.get_children(root_items[0]):
            self.update_check_state(child_id, "checked")

    def uncheck_all(self):
        root_items = self.tree.get_children()
        if not root_items: return
        for child_id in self.tree.get_children(root_items[0]):
            self.update_check_state(child_id, "unchecked")