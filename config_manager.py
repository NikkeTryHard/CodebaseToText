# config_manager.py
import configparser
import os
from constants import DEFAULT_IGNORED_ITEMS

class ConfigManager:
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()

        # Define default settings
        defaults = {
            'Settings': {
                'width': '800',
                'height': '700',
                'last_folder': '',
                'ignore_list': '.log, .tmp, venv',
                'theme': 'dark'
            }
        }

        # Attempt to read the existing config file.
        # If it's malformed or doesn't exist, we'll proceed with defaults.
        try:
            if os.path.exists(config_file):
                self.config.read(config_file)
        except configparser.Error:
            print(f"Warning: Could not parse '{config_file}'. A new one will be created with defaults.")

        # Check for missing sections and keys and apply defaults if necessary
        config_was_modified = False
        for section, keys in defaults.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
                config_was_modified = True
            for key, value in keys.items():
                if not self.config.has_option(section, key):
                    self.config.set(section, key, value)
                    config_was_modified = True
        
        # If the file was created or updated with default values, save it.
        # This ensures that a complete config file is always present.
        if config_was_modified:
            self.save_config()

    def get_setting(self, section, key, fallback=None):
        return self.config.get(section, key, fallback=fallback)

    def set_setting(self, section, key, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))

    def save_config(self):
        """Saves the current in-memory configuration to the file."""
        try:
            with open(self.config_file, 'w') as f:
                self.config.write(f)
        except IOError:
            print(f"Error: Could not write to config file at '{self.config_file}'.")

    def get_ignored_set(self):
        """Returns a set of items to ignore, combining defaults with user config."""
        user_list_str = self.get_setting('Settings', 'ignore_list', '')
        user_list = {item.strip() for item in user_list_str.split(',') if item.strip()}
        return DEFAULT_IGNORED_ITEMS.union(user_list)