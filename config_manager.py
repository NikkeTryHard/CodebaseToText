# config_manager.py
import configparser
import os
from constants import DEFAULT_IGNORED_ITEMS

class ConfigManager:
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        if os.path.exists(config_file):
            self.config.read(config_file)
        else:
            self._create_default_config()

    def _create_default_config(self):
        self.config['Settings'] = {
            'width': '800',
            'height': '700',
            'last_folder': '',
            'ignore_list': '.log, .tmp, venv',
            'theme': 'dark'
        }
        self.save_config()

    def get_setting(self, section, key, fallback=None):
        return self.config.get(section, key, fallback=fallback)

    def set_setting(self, section, key, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))

    def save_config(self):
        with open(self.config_file, 'w') as f:
            self.config.write(f)

    def get_ignored_set(self):
        """Returns a set of items to ignore, combining defaults with user config."""
        user_list_str = self.get_setting('Settings', 'ignore_list', '')
        user_list = {item.strip() for item in user_list_str.split(',') if item.strip()}
        return DEFAULT_IGNORED_ITEMS.union(user_list)