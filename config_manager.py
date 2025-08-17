# config_manager.py
import configparser
import os
from constants import DEFAULT_IGNORED_ITEMS

class ConfigManager:
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()

        # These defaults are now used as fallbacks if a key is missing,
        # rather than being written to the file automatically.
        self.defaults = {
            'Settings': {
                'width': '800',
                'height': '700',
                'last_folder': '',
                'ignore_list': '', # The default is now an empty string.
                'theme': 'dark'
            }
        }
        
        # We only create a new config file if it's completely missing.
        # We will no longer "repair" an existing file on startup.
        if not os.path.exists(self.config_file):
            print(f"Config file '{self.config_file}' not found. Creating with default values.")
            self.config['Settings'] = self.defaults['Settings']
            self.save_config()
        else:
            self.config.read(self.config_file)

    def get_setting(self, section, key):
        """
        Gets a setting from the config file. If the setting is not found,
        it falls back to the value defined in the self.defaults dictionary.
        """
        fallback_value = self.defaults.get(section, {}).get(key)
        return self.config.get(section, key, fallback=fallback_value)

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
        """Returns a set of items to ignore from the config file and constants."""
        user_list_str = self.get_setting('Settings', 'ignore_list')
        user_list = {item.strip() for item in user_list_str.split(',') if item.strip()}
        # Combine the hardcoded set (which should be empty) with the user's set.
        return DEFAULT_IGNORED_ITEMS.union(user_list)