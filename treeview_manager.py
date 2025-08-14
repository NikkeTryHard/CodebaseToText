# treeview_manager.py
import os
import tkinter.font as tkfont
from tkinter import ttk
from constants import CHECKED_EMOJI, UNCHECKED_EMOJI
import file_processor

class TreeViewManager:
    """
    Manages the Treeview widget, including population, item checking, and event handling.
    """
    def __init__(self, tree_widget, root_window, log_callback, ignored_items):
        """
        Initializes the TreeViewManager.

        Args:
            tree_widget (ttk.Treeview): The treeview widget to manage.
            root_window (tk.Tk): The root window of the application.
            log_callback (function): A function to call for logging messages.
            ignored_items (set): A set of filenames/directories to ignore.
        """
        self.tree = tree_widget
        self.root = root_window
        self.log_message = log_callback
        self.ignored_items = ignored_items
        self.tree_font = self._get_tree_font()
        self.tree.bind("<Button-1>", self.handle_tree_click)

    def _get_file_details(self, file_path):
        """Generate a formatted string with file type and line count."""
        if file_processor._is_binary_file(file_path):
            return " [binary]"
        
        details = []
        lang = file_processor.get_language_identifier(file_path)
        if lang and lang != 'text':
            details.append(lang)
            
        line_count = file_processor._get_line_count(file_path)
        if line_count > 0:
            details.append(f"{line_count} lines")
            
        return f"  [{' | '.join(details)}]" if details else ""

    def _get_tree_font(self):
        """
        Gets the font used by the Treeview widget.

        Returns:
            tkfont.Font: The font object.
        """
        try:
            style = ttk.Style()
            self.root.update_idletasks()
            font_name = style.lookup("Ttreeview", "font")
            return tkfont.Font(font=font_name)
        except Exception:
            return tkfont.Font()

    def populate_treeview(self, root_path):
        """
        Populates the treeview with the contents of a directory.

        Args:
            root_path (str): The path to the root directory.
        """
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        if not root_path:
            return
            
        root_node = self.tree.insert("", "end", text=f" {CHECKED_EMOJI} {os.path.basename(root_path)}", open=True, values=[root_path, "checked"])
        self._populate_recursive(root_path, root_node)

    def _populate_recursive(self, path, parent_node):
        try:
            items = sorted(os.listdir(path), key=lambda item: (not os.path.isdir(os.path.join(path, item)), item.lower()))
            for item in items:
                if item in self.ignored_items:
                    continue

                item_path = os.path.join(path, item)
                node_text = f" {CHECKED_EMOJI} {item}"

                if os.path.isfile(item_path):
                    details = self._get_file_details(item_path)
                    node_text += details

                node = self.tree.insert(parent_node, "end", text=node_text, open=False, values=[item_path, "checked"])
                if os.path.isdir(item_path):
                    self._populate_recursive(item_path, node)
        except (PermissionError, FileNotFoundError) as e:
            self.log_message(f"Warning: Cannot access {e.filename}. Skipping.")

    def handle_tree_click(self, event):
        """
        Handles click events on the treeview.

        A click on the checkbox toggles the check state.
        A click on the text expands/collapses a directory.

        Args:
            event: The tkinter event object.
        """
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
        try:
            bbox = self.tree.bbox(item_id, "text")
        except Exception:
            return
        if not bbox:
            return
            
        item_text = self.tree.item(item_id, "text")
        main_text = item_text.split('[')[0]
        checkbox_area_text = f" {CHECKED_EMOJI} "
        checkbox_width = self.tree_font.measure(checkbox_area_text)
        text_width = self.tree_font.measure(main_text)

        if bbox[0] <= event.x < bbox[0] + checkbox_width:
            self.toggle_check_state(item_id)
        elif bbox[0] + checkbox_width <= event.x < bbox[0] + text_width:
            values = self.tree.item(item_id, "values")
            if values and os.path.isdir(values[0]):
                self.tree.item(item_id, open=not self.tree.item(item_id, "open"))

    def toggle_check_state(self, item_id):
        """
        Toggles the check state of a treeview item.

        Args:
            item_id (str): The ID of the treeview item.
        """
        values = self.tree.item(item_id, "values")
        if not values:
            return
        new_state = "unchecked" if values[1] == "checked" else "checked"
        self.update_check_state(item_id, new_state)

    def update_check_state(self, item_id, state):
        """
        Updates the check state of a treeview item and its children.

        Args:
            item_id (str): The ID of the treeview item.
            state (str): The new state ('checked' or 'unchecked').
        """
        current_text = self.tree.item(item_id, "text")
        
        base_text, _, details = current_text.partition('  [')
        if details:
            details = '  [' + details

        text_parts = base_text.strip().split(' ', 1)
        item_name = text_parts[1] if len(text_parts) > 1 else ""
        
        emoji = CHECKED_EMOJI if state == "checked" else UNCHECKED_EMOJI
        new_text = f" {emoji} {item_name}{details}"
        
        self.tree.item(item_id, text=new_text, values=[self.tree.item(item_id, "values")[0], state])
        for child_id in self.tree.get_children(item_id):
            self.update_check_state(child_id, state)

    def get_checked_files(self):
        """
        Recursively gets a list of all checked files in the treeview.

        Returns:
            list: A list of paths to the checked files.
        """
        checked_files = []
        def _recurse_tree(item_id):
            values = self.tree.item(item_id, "values")
            if not values:
                return
            path, state = values[0], values[1]
            if state == "checked":
                if os.path.isfile(path):
                    checked_files.append(path)
                for child_id in self.tree.get_children(item_id):
                    _recurse_tree(child_id)
        root_items = self.tree.get_children()
        if root_items:
            _recurse_tree(root_items[0])
        return checked_files

    def check_all(self):
        """Checks all items in the treeview."""
        for item_id in self.tree.get_children():
            self.update_check_state(item_id, "checked")

    def uncheck_all(self):
        """Unchecks all items in the treeview."""
        for item_id in self.tree.get_children():
            self.update_check_state(item_id, "unchecked")

    def check_selected(self):
        """Checks the currently selected items in the treeview."""
        for item_id in self.tree.selection():
            self.update_check_state(item_id, "checked")

    def uncheck_selected(self):
        """Unchecks the currently selected items in the treeview."""
        for item_id in self.tree.selection():
            self.update_check_state(item_id, "unchecked")