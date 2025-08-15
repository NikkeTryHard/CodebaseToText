# config_manager.py
import configparser
import os
from constants import DEFAULT_IGNORED_ITEMS

class ConfigManager:
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        
        # Safer Initialization:
        # 1. Set the default values in memory first.
        self._set_defaults()
        
        # 2. If the config file exists, read it to override the defaults.
        if os.path.exists(config_file):
            try:
                self.config.read(config_file)
            except configparser.Error:
                # If the file is malformed, we'll proceed with defaults
                # and overwrite the bad file on the next save.
                print(f"Warning: Could not parse '{config_file}'. Using default settings.")
        else:
            # 3. If the file doesn't exist, save the defaults to create it.
            self.save_config()

    def _set_defaults(self):
        """Sets the default configuration values in the config object."""
        self.config['Settings'] = {
            'width': '800',
            'height': '700',
            'last_folder': '',
            'ignore_list': '.log, .tmp, venv',
            'theme': 'dark'
        }

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