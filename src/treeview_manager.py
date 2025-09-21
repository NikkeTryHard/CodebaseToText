# treeview_manager.py
import os
import tkinter as tk
from tkinter import PhotoImage, messagebox
# FIX: Removed unused 'time' import (Ruff F401)

class TreeViewManager:
    """
    Manages the Treeview widget, including population from a data structure,
    item checking, and event handling using robust image-based checkboxes.
    """
    def __init__(self, tree_widget, root_window, log_callback, ignored_items, resource_path_func, ignore_callback=None):
        self.tree = tree_widget
        self.root = root_window
        self.log_message = log_callback
        self.ignored_items = ignored_items
        self.ignore_callback = ignore_callback
        self.resource_path = resource_path_func
        self.scanned_data = None
        self.animation_running = False
        self.last_click_time = 0
        self.double_click_delay = 300  # milliseconds

        try:
            self.checked_img = PhotoImage(file=self.resource_path("assets/checked.png"))
            self.unchecked_img = PhotoImage(file=self.resource_path("assets/unchecked.png"))
            self.ignored_img = PhotoImage(file=self.resource_path("assets/unchecked.png"))
        except Exception as e:
            self.log_message(f"Error loading checkbox images: {e}")
            # Fallback to text-based checkboxes if images fail
            self.checked_img = self.unchecked_img = self.ignored_img = None
            self._setup_fallback_checkboxes()

        self.tree.bind("<Button-1>", self.handle_tree_click)
        self.tree.bind("<space>", self.handle_spacebar_press)
        self.tree.bind("<Double-Button-1>", self.handle_double_click)
        self.tree.bind("<Return>", self.handle_enter_press)
        
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Button-2>", self.show_context_menu)
        self.tree.bind("<Control-Button-1>", self.show_context_menu)
        
        self.tree.bind("<Key>", self.handle_key_press)

    def _setup_fallback_checkboxes(self):
        """Setup fallback text-based checkboxes if images fail to load."""
        self.use_text_checkboxes = True
        self.log_message("Using text-based checkboxes as fallback")

    def clear_tree(self):
        """Removes all items from the treeview with animation."""
        if self.animation_running:
            return
            
        self.animation_running = True
        items = self.tree.get_children()
        
        if not items:
            self.animation_running = False
            return
            
        def animate_clear(index=0):
            if index >= len(items):
                self.animation_running = False
                return
                
            try:
                self.tree.delete(items[index])
            except Exception:
                pass  # Item might already be deleted
                
            self.root.after(10, lambda: animate_clear(index + 1))
        
        animate_clear()

    def populate_from_data(self, root_node_data):
        """Populates the treeview using a pre-scanned dictionary structure with animation."""
        self.scanned_data = root_node_data
        self.clear_tree()
        if not root_node_data:
            return
        
        self.root.after(100, lambda: self._populate_with_animation(root_node_data))

    def _populate_with_animation(self, root_node_data, delay=5):
        """Populates the treeview with animation effects."""
        self.clear_tree()
        
        def delayed_populate():
            try:
                root_item = self.tree.insert("", "end", text=f" 📁 {root_node_data['name']}", 
                                          open=True, image=self.checked_img, 
                                          values=(root_node_data['path'], "root_state"))
                
                if root_node_data.get('children'):
                    self._populate_recursive_animated(root_node_data['children'], root_item, delay)
                    
            except Exception as e:
                self.log_message(f"Error populating tree: {e}")
                messagebox.showerror("Error", f"Failed to populate tree view: {e}")
        
        self.root.after(delay, delayed_populate)

    def _populate_recursive_animated(self, children_data, parent_node, delay=50):
        """Populates children with animation effects."""
        for i, item_data in enumerate(children_data):
            try:
                self.root.after(delay * (i + 1), 
                              lambda data=item_data, parent=parent_node: 
                              self._insert_item_animated(data, parent))
            except Exception as e:
                self.log_message(f"Error scheduling item insertion: {e}")

    def _insert_item_animated(self, item_data, parent_node):
        """Inserts a single item with animation."""
        try:
            annotation = self._get_item_annotation(item_data)
            node_text = f" {'📁' if item_data['is_dir'] else '📄'} {item_data['name']}{annotation}"
            
            if item_data['is_ignored']:
                item = self.tree.insert(parent_node, "end", text=node_text, open=False, 
                                      image=self.ignored_img, values=(item_data['path'], "ignored"), 
                                      tags=('ignored',))
            else:
                item = self.tree.insert(parent_node, "end", text=node_text, open=False, 
                                      image=self.checked_img, values=(item_data['path'], "checked"))
                
                if item_data.get('children'):
                    self._populate_recursive_animated(item_data['children'], item, 1)
                    
        except Exception as e:
            self.log_message(f"Error inserting item {item_data.get('name', 'unknown')}: {e}")

    def _get_item_annotation(self, item_data):
        """Get formatted annotation for tree items."""
        annotation = ""
        try:
            if not item_data['is_dir'] and not item_data['is_ignored']:
                error = item_data.get('error')
                if error:
                    annotation = f"  ⚠️ [{error}]"
                elif item_data.get('line_count') is not None:
                    lines = item_data['line_count']
                    chars = item_data.get('char_count', 0)
                    annotation = f"  📊 [{lines} lines, {chars} chars]"
                elif item_data.get('size'):
                    size_kb = item_data['size'] / 1024
                    if size_kb > 1024:
                        annotation = f"  💾 [{size_kb/1024:.1f} MB]"
                    else:
                        annotation = f"  💾 [{size_kb:.1f} KB]"
        except Exception as e:
            self.log_message(f"Error getting annotation: {e}")
            
        return annotation

    def handle_tree_click(self, event):
        """Handle single click events with improved logic."""
        item_id = self.tree.identify_row(event.y)
        
        if not item_id:
            return
            
        element = self.tree.identify_element(event.x, event.y)
        
        if "image" in element:
            self._handle_checkbox_click(item_id, event)
            return "break"
        elif "text" in element:
            self._handle_text_click(item_id, event)
            return "break"

    def _handle_checkbox_click(self, item_id, event):
        """Handle checkbox click with visual feedback."""
        try:
            values = self.tree.item(item_id, "values")
            if not values or values[1] in ["ignored", "root_state"]:
                return
                
            self._highlight_item_temporarily(item_id)
            
            new_state = "unchecked" if values[1] == "checked" else "checked"
            self.update_check_state(item_id, new_state)
            
            item_name = self.tree.item(item_id, "text").strip()
            self.log_message(f"{'Checked' if new_state == 'checked' else 'Unchecked'}: {item_name}")
            
        except Exception as e:
            self.log_message(f"Error handling checkbox click: {e}")

    def _handle_text_click(self, item_id, event):
        """Handle text click for folder expansion."""
        try:
            values = self.tree.item(item_id, "values")
            if values and os.path.isdir(values[0]):
                current_state = self.tree.item(item_id, "open")
                self.tree.item(item_id, open=not current_state)
                
                self._highlight_item_temporarily(item_id)
                
        except Exception as e:
            self.log_message(f"Error handling text click: {e}")

    def _highlight_item_temporarily(self, item_id):
        """Highlight an item temporarily for visual feedback."""
        try:
            original_tags = list(self.tree.item(item_id, "tags"))
            highlight_tag = "highlight"
            
            if highlight_tag not in original_tags:
                self.tree.item(item_id, tags=original_tags + [highlight_tag])
                
            self.root.after(200, lambda: self._remove_highlight(item_id, original_tags))
            
        except Exception as e:
            self.log_message(f"Error highlighting item: {e}")

    def _remove_highlight(self, item_id, original_tags):
        """Remove highlight from an item."""
        try:
            current_tags = list(self.tree.item(item_id, "tags"))
            if "highlight" in current_tags:
                current_tags.remove("highlight")
                self.tree.item(item_id, tags=current_tags)
        except Exception:
            pass  # Item might have been deleted

    def handle_double_click(self, event):
        """Handle double-click events."""
        item_id = self.tree.identify_row(event.y)
        if item_id:
            values = self.tree.item(item_id, "values")
            if values and os.path.isfile(values[0]):
                self._open_file(values[0])

    def handle_enter_press(self, event):
        """Handle Enter key press for selected items."""
        for item_id in self.tree.selection():
            values = self.tree.item(item_id, "values")
            if values and os.path.isfile(values[0]):
                self._open_file(values[0])
            elif values and os.path.isdir(values[0]):
                current_state = self.tree.item(item_id, "open")
                self.tree.item(item_id, open=not current_state)

    def _open_file(self, file_path):
        """Open file in default application."""
        try:
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                os.startfile(file_path)  # type: ignore
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", file_path])
            else:  # Linux
                subprocess.run(["xdg-open", file_path])
                
        except Exception as e:
            self.log_message(f"Could not open file {file_path}: {e}")

    def handle_spacebar_press(self, event):
        """Handle spacebar press for selected items."""
        for item_id in self.tree.selection():
            self.toggle_check_state(item_id)
        return "break"

    def handle_key_press(self, event):
        """Handle additional keyboard shortcuts."""
        if event.keysym == 'a' and event.state & 4:  # Ctrl+A
            self.check_all()
            return "break"
        elif event.keysym == 'u' and event.state & 4:  # Ctrl+U
            self.uncheck_all()
            return "break"
        elif event.keysym == 'r' and event.state & 4:  # Ctrl+R
            self._refresh_tree()
            return "break"

    # FIX: Moved _refresh_tree method definition here to resolve Pylance error.
    def _refresh_tree(self):
        """Refresh the tree view."""
        try:
            self.log_message("Tree refresh requested")
        except Exception as e:
            self.log_message(f"Error refreshing tree: {e}")

    def show_context_menu(self, event):
        """Show context menu for right-click."""
        self.log_message(f"Context menu triggered by event: {event.type} (Button {event.num})")
        try:
            item_id = self.tree.identify_row(event.y)
            if not item_id:
                self.log_message("Context menu aborted: no item found under cursor.")
                return
                
            self.tree.selection_set(item_id)
                
            context_menu = tk.Menu(self.root, tearoff=0)
            
            values = self.tree.item(item_id, "values")
            if values:
                relative_path = os.path.relpath(values[0], self.root.global_app_instance.root_dir.get())
                context_menu.add_command(label=f"Ignore '{os.path.basename(values[0])}'",
                                      command=lambda: self._ignore_item(relative_path))
                context_menu.add_separator()

            if values and os.path.isfile(values[0]):
                context_menu.add_command(label="Open File",
                                      command=lambda: self._open_file(values[0]))
                context_menu.add_command(label="Copy Path",
                                      command=lambda: self._copy_to_clipboard(values[0]))
                context_menu.add_separator()
            
            context_menu.add_command(label="Check Item",
                                  command=lambda: self.update_check_state(item_id, "checked"))
            context_menu.add_command(label="Uncheck Item", 
                                  command=lambda: self.update_check_state(item_id, "unchecked"))
            
            if values and values[1] not in ["ignored", "root_state"]:
                context_menu.add_separator()
                context_menu.add_command(label="Check All Children", 
                                      command=lambda: self._check_all_children(item_id))
                context_menu.add_command(label="Uncheck All Children", 
                                      command=lambda: self._uncheck_all_children(item_id))
            
            context_menu.tk_popup(event.x_root, event.y_root)
            
        except Exception as e:
            self.log_message(f"Error showing context menu: {e}")

    def _ignore_item(self, path_to_ignore):
        """Handle the ignore item action."""
        if self.ignore_callback:
            self.ignore_callback(path_to_ignore)

    def _copy_to_clipboard(self, text):
        """Copy text to clipboard."""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.log_message("Path copied to clipboard")
        except Exception as e:
            self.log_message(f"Error copying to clipboard: {e}")

    def _check_all_children(self, item_id):
        """Check all children of an item."""
        self._update_children_state(item_id, "checked")

    def _uncheck_all_children(self, item_id):
        """Uncheck all children of an item."""
        self._update_children_state(item_id, "unchecked")

    def _update_children_state(self, item_id, state):
        """Update the state of all children of an item."""
        try:
            for child_id in self.tree.get_children(item_id):
                values = self.tree.item(child_id, "values")
                if values and values[1] not in ["ignored", "root_state"]:
                    self.update_check_state(child_id, state)
        except Exception as e:
            self.log_message(f"Error updating children state: {e}")

    def toggle_check_state(self, item_id):
        """Toggle the check state of an item with validation."""
        try:
            values = self.tree.item(item_id, "values")
            if not values or values[1] in ["ignored", "root_state"]:
                return
                
            new_state = "unchecked" if values[1] == "checked" else "checked"
            self.update_check_state(item_id, new_state)
            
        except Exception as e:
            self.log_message(f"Error toggling check state: {e}")

    def update_check_state(self, item_id, state):
        """Update the check state of an item with improved error handling."""
        try:
            values = self.tree.item(item_id, "values")
            if not values or values[1] in ["ignored", "root_state"]:
                return

            new_image = self.checked_img if state == "checked" else self.unchecked_img
            self.tree.item(item_id, image=new_image, values=(values[0], state))
            
            self._update_children_recursive(item_id, state)
            
        except Exception as e:
            self.log_message(f"Error updating check state: {e}")

    def _update_children_recursive(self, item_id, state):
        """Recursively update all children of an item."""
        try:
            for child_id in self.tree.get_children(item_id):
                values = self.tree.item(child_id, "values")
                if values and values[1] not in ["ignored", "root_state"]:
                    new_image = self.checked_img if state == "checked" else self.unchecked_img
                    self.tree.item(child_id, image=new_image, values=(values[0], state))
                    
                    self._update_children_recursive(child_id, state)
                    
        except Exception as e:
            self.log_message(f"Error updating children recursively: {e}")

    def get_checked_files(self):
        """Get all checked files with improved error handling."""
        checked_files = []
        try:
            def _recurse(item_id):
                try:
                    values = self.tree.item(item_id, "values")
                    if not values:
                        return
                    path, state = values[0], values[1]
                    if state == "checked" or state == "root_state":
                        if os.path.isfile(path) and state == "checked":
                            checked_files.append(path)
                        if os.path.isdir(path):
                            for child in self.tree.get_children(item_id):
                                _recurse(child)
                except Exception as e:
                    self.log_message(f"Error processing tree item: {e}")
                    
            for item in self.tree.get_children():
                _recurse(item)
                
        except Exception as e:
            self.log_message(f"Error getting checked files: {e}")
            
        return checked_files

    def check_all(self):
        """Check all items with visual feedback."""
        try:
            root_items = self.tree.get_children()
            if not root_items:
                return
                
            self._animate_check_all(root_items[0])
            
        except Exception as e:
            self.log_message(f"Error checking all items: {e}")

    def _animate_check_all(self, root_item, delay=10):
        """Animate checking all items."""
        children = self.tree.get_children(root_item)
        if not children:
            return
            
        def animate_check(index=0):
            if index >= len(children):
                return
                
            try:
                child_id = children[index]
                values = self.tree.item(child_id, "values")
                if values and values[1] not in ["ignored", "root_state"]:
                    self.update_check_state(child_id, "checked")
            except Exception:
                pass
                
            self.root.after(delay, lambda: animate_check(index + 1))
            
        animate_check()

    def uncheck_all(self):
        """Uncheck all items with visual feedback."""
        try:
            root_items = self.tree.get_children()
            if not root_items:
                return
                
            self._animate_uncheck_all(root_items[0])
            
        except Exception as e:
            self.log_message(f"Error unchecking all items: {e}")

    def _animate_uncheck_all(self, root_item, delay=10):
        """Animate unchecking all items."""
        children = self.tree.get_children(root_item)
        if not children:
            return
            
        def animate_uncheck(index=0):
            if index >= len(children):
                return
                
            try:
                child_id = children[index]
                values = self.tree.item(child_id, "values")
                if values and values[1] not in ["ignored", "root_state"]:
                    self.update_check_state(child_id, "unchecked")
            except Exception:
                pass
                
            self.root.after(delay, lambda: animate_uncheck(index + 1))
            
        animate_uncheck()

    def sort_tree_data(self, sort_key):
        """Sort the tree data and repopulate the view."""
        if not self.scanned_data:
            self.log_message("No data to sort.")
            return
        
        self.log_message(f"Sorting by {sort_key}")

        def get_sort_value(item):
            if sort_key == 'Lines':
                if item.get('is_dir'):
                    return -1
                return item.get('line_count') or 0
            elif sort_key == 'Characters':
                if item.get('is_dir'):
                    return -1
                return item.get('char_count') or 0
            else: # 'Name'
                return item.get('name', '').lower()

        def sort_recursive(node):
            if not node:
                return
            if node.get('children'):
                is_descending = sort_key in ['Lines', 'Characters']
                
                node['children'].sort(key=lambda x: (not x.get('is_dir', False), get_sort_value(x)), reverse=is_descending)
                
                if node is self.scanned_data:
                    sorted_names = [child['name'] for child in node['children'][:5]]
                    self.log_message(f"Top 5 sorted items: {sorted_names}")

                for child in node['children']:
                    sort_recursive(child)
        
        sort_recursive(self.scanned_data)
        self.populate_from_data(self.scanned_data)

    def get_tree_info(self):
        """Get information about the current tree state."""
        try:
            total_items = 0
            checked_items = 0
            ignored_items = 0
            
            def count_items(item_id):
                nonlocal total_items, checked_items, ignored_items
                total_items += 1
                
                values = self.tree.item(item_id, "values")
                if values:
                    if values[1] == "checked":
                        checked_items += 1
                    elif values[1] == "ignored":
                        ignored_items += 1
                        
                for child in self.tree.get_children(item_id):
                    count_items(child)
            
            for item in self.tree.get_children():
                count_items(item)
                
            return {
                'total': total_items,
                'checked': checked_items,
                'ignored': ignored_items,
                'unchecked': total_items - checked_items - ignored_items
            }
            
        except Exception as e:
            self.log_message(f"Error getting tree info: {e}")
            return {'total': 0, 'checked': 0, 'ignored': 0, 'unchecked': 0}