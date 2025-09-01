# config_manager.py
import configparser
import os
import json
from constants import DEFAULT_IGNORED_ITEMS

class ConfigManager:
    """Enhanced configuration manager with better error handling and validation."""
    
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        
        # Enhanced defaults with new settings
        self.defaults = {
            'Settings': {
                'width': '900',
                'height': '800',
                'last_folder': '',
                'ignore_list': '',
                'theme': 'dark',
                'max_file_size': '10',
                'auto_save': 'True',
                'verbose': 'False',
                'window_x': '100',
                'window_y': '100',
                'max_recent_folders': '5',
                'enable_animations': 'True',
                'enable_tooltips': 'True'
            },
            'Advanced': {
                'scan_timeout': '300',
                'max_threads': '4',
                'chunk_size': '50000',
                'enable_caching': 'True',
                'cache_size': '100'
            }
        }
        
        # Initialize configuration
        self._initialize_config()

    def _initialize_config(self):
        """Initialize configuration with error handling."""
        try:
            # Check if config file exists
            if not os.path.exists(self.config_file):
                self._create_default_config()
            else:
                # Read existing config
                self.config.read(self.config_file)
                
                # Validate and repair config if needed
                self._validate_and_repair_config()
                
        except Exception as e:
            print(f"Error initializing configuration: {e}")
            # Create minimal config as fallback
            self._create_minimal_config()

    def _create_default_config(self):
        """Create a new configuration file with default values."""
        try:
            print(f"Config file '{self.config_file}' not found. Creating with default values.")
            
            # Create sections and set defaults
            for section, options in self.defaults.items():
                if not self.config.has_section(section):
                    self.config.add_section(section)
                for key, value in options.items():
                    self.config.set(section, key, value)
            
            # Save the new config
            self.save_config()
            
        except Exception as e:
            print(f"Error creating default config: {e}")

    def _create_minimal_config(self):
        """Create minimal configuration as fallback."""
        try:
            self.config['Settings'] = {
                'width': '800',
                'height': '600',
                'theme': 'dark'
            }
            self.save_config()
        except Exception as e:
            print(f"Error creating minimal config: {e}")

    def _validate_and_repair_config(self):
        """Validate existing config and repair if needed."""
        try:
            # Check for missing sections
            for section, options in self.defaults.items():
                if not self.config.has_section(section):
                    self.config.add_section(section)
                    print(f"Added missing section: {section}")
                
                # Check for missing options
                for key, default_value in options.items():
                    if not self.config.has_option(section, key):
                        self.config.set(section, key, default_value)
                        print(f"Added missing option: {section}.{key} = {default_value}")
            
            # Validate specific values
            self._validate_numeric_values()
            self._validate_boolean_values()
            
        except Exception as e:
            print(f"Error validating config: {e}")

    def _validate_numeric_values(self):
        """Validate numeric configuration values."""
        try:
            # Validate width and height
            width = self.get_setting('Settings', 'width')
            height = self.get_setting('Settings', 'height')
            
            if not width.isdigit() or int(width) < 400:
                self.config.set('Settings', 'width', '900')
            if not height.isdigit() or int(height) < 300:
                self.config.set('Settings', 'height', '800')
            
            # Validate max file size
            max_size = self.get_setting('Settings', 'max_file_size')
            if not max_size.isdigit() or int(max_size) < 1:
                self.config.set('Settings', 'max_file_size', '10')
                
        except Exception as e:
            print(f"Error validating numeric values: {e}")

    def _validate_boolean_values(self):
        """Validate boolean configuration values."""
        try:
            boolean_settings = ['auto_save', 'verbose', 'enable_animations', 'enable_tooltips', 'enable_caching']
            
            for setting in boolean_settings:
                value = self.get_setting('Settings', setting, fallback='True')
                if value.lower() not in ['true', 'false']:
                    self.config.set('Settings', setting, 'True')
                    
        except Exception as e:
            print(f"Error validating boolean values: {e}")

    def get_setting(self, section, key, fallback=None):
        """
        Gets a setting from the config file with enhanced fallback handling.
        
        Args:
            section: Configuration section name
            key: Configuration key name
            fallback: Fallback value if not found
            
        Returns:
            The configuration value or fallback
        """
        try:
            # First try to get from config
            if self.config.has_section(section) and self.config.has_option(section, key):
                return self.config.get(section, key)
            
            # Fallback to defaults
            if fallback is not None:
                return fallback
                
            # Use default from self.defaults
            return self.defaults.get(section, {}).get(key, '')
            
        except Exception as e:
            print(f"Error getting setting {section}.{key}: {e}")
            # Return fallback or empty string
            return fallback if fallback is not None else ''

    def set_setting(self, section, key, value):
        """
        Sets a configuration value with validation.
        
        Args:
            section: Configuration section name
            key: Configuration key name
            value: Value to set
        """
        try:
            # Ensure section exists
            if not self.config.has_section(section):
                self.config.add_section(section)
            
            # Validate value based on key
            validated_value = self._validate_setting_value(section, key, value)
            
            # Set the value
            self.config.set(section, key, str(validated_value))
            
        except Exception as e:
            print(f"Error setting setting {section}.{key}: {e}")

    def _validate_setting_value(self, section, key, value):
        """Validate a setting value based on its type."""
        try:
            # Numeric validation
            if key in ['width', 'height', 'max_file_size', 'scan_timeout', 'max_threads', 'chunk_size', 'cache_size']:
                try:
                    num_value = int(value)
                    if key in ['width', 'height']:
                        return max(400, min(3000, num_value))  # Reasonable bounds
                    elif key == 'max_file_size':
                        return max(1, min(1000, num_value))  # 1MB to 1GB
                    elif key == 'scan_timeout':
                        return max(30, min(1800, num_value))  # 30s to 30min
                    elif key == 'max_threads':
                        return max(1, min(16, num_value))  # 1 to 16 threads
                    elif key == 'chunk_size':
                        return max(1000, min(1000000, num_value))  # 1KB to 1MB
                    elif key == 'cache_size':
                        return max(10, min(1000, num_value))  # 10 to 1000 items
                except ValueError:
                    return self.defaults.get(section, {}).get(key, value)
            
            # Boolean validation
            elif key in ['auto_save', 'verbose', 'enable_animations', 'enable_tooltips', 'enable_caching']:
                if isinstance(value, bool):
                    return value
                elif isinstance(value, str):
                    return value.lower() in ['true', '1', 'yes', 'on']
                else:
                    return bool(value)
            
            # String validation
            elif key == 'theme':
                return value if value in ['dark', 'light'] else 'dark'
            elif key == 'last_folder':
                return str(value) if value else ''
            else:
                return str(value)
                
        except Exception as e:
            print(f"Error validating setting value {section}.{key}: {e}")
            return value

    def save_config(self):
        """Saves the current configuration to file with error handling."""
        try:
            # Create directory if it doesn't exist
            config_dir = os.path.dirname(self.config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            # Write configuration
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
                
            print(f"Configuration saved to {self.config_file}")
            
        except IOError as e:
            print(f"Error: Could not write to config file at '{self.config_file}': {e}")
        except Exception as e:
            print(f"Unexpected error saving config: {e}")

    def get_ignored_set(self):
        """Returns a set of items to ignore with enhanced parsing."""
        try:
            user_list_str = self.get_setting('Settings', 'ignore_list')
            user_list = set()
            
            if user_list_str:
                # Split by comma and newline for flexibility
                items = []
                for line in user_list_str.split(','):
                    items.extend(line.split('\n'))
                
                # Clean and filter items
                for item in items:
                    cleaned_item = item.strip()
                    if cleaned_item and not cleaned_item.startswith('#'):
                        user_list.add(cleaned_item)
            
            # Combine with default ignored items
            return DEFAULT_IGNORED_ITEMS.union(user_list)
            
        except Exception as e:
            print(f"Error getting ignored set: {e}")
            return DEFAULT_IGNORED_ITEMS

    def get_recent_folders(self):
        """Get list of recently used folders."""
        try:
            recent_str = self.get_setting('Settings', 'recent_folders', fallback='[]')
            try:
                recent_list = json.loads(recent_str)
                if isinstance(recent_list, list):
                    return recent_list
            except (json.JSONDecodeError, TypeError):
                pass
            return []
        except Exception as e:
            print(f"Error getting recent folders: {e}")
            return []

    def add_recent_folder(self, folder_path):
        """Add a folder to the recent folders list."""
        try:
            recent_folders = self.get_recent_folders()
            
            # Remove if already exists
            if folder_path in recent_folders:
                recent_folders.remove(folder_path)
            
            # Add to beginning
            recent_folders.insert(0, folder_path)
            
            # Limit to max_recent_folders
            max_recent = int(self.get_setting('Settings', 'max_recent_folders', fallback='5'))
            recent_folders = recent_folders[:max_recent]
            
            # Save back to config
            self.set_setting('Settings', 'recent_folders', json.dumps(recent_folders))
            
        except Exception as e:
            print(f"Error adding recent folder: {e}")

    def get_advanced_setting(self, key, fallback=None):
        """Get an advanced setting with fallback."""
        return self.get_setting('Advanced', key, fallback)

    def set_advanced_setting(self, key, value):
        """Set an advanced setting."""
        self.set_setting('Advanced', key, value)

    def reset_to_defaults(self):
        """Reset all settings to default values."""
        try:
            # Clear existing config
            self.config.clear()
            
            # Recreate with defaults
            for section, options in self.defaults.items():
                if not self.config.has_section(section):
                    self.config.add_section(section)
                for key, value in options.items():
                    self.config.set(section, key, value)
            
            # Save the reset config
            self.save_config()
            print("Configuration reset to defaults")
            
        except Exception as e:
            print(f"Error resetting to defaults: {e}")

    def export_config(self, export_path):
        """Export configuration to a file."""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            print(f"Configuration exported to {export_path}")
            return True
        except Exception as e:
            print(f"Error exporting configuration: {e}")
            return False

    def import_config(self, import_path):
        """Import configuration from a file."""
        try:
            # Read the import file
            import_config = configparser.ConfigParser()
            import_config.read(import_path)
            
            # Merge with current config
            for section in import_config.sections():
                if not self.config.has_section(section):
                    self.config.add_section(section)
                for key, value in import_config.items(section):
                    self.config.set(section, key, value)
            
            # Save merged config
            self.save_config()
            print(f"Configuration imported from {import_path}")
            return True
            
        except Exception as e:
            print(f"Error importing configuration: {e}")
            return False

    def get_config_summary(self):
        """Get a summary of current configuration."""
        try:
            summary = {}
            for section in self.config.sections():
                summary[section] = dict(self.config.items(section))
            return summary
        except Exception as e:
            print(f"Error getting config summary: {e}")
            return {}

    def validate_config(self):
        """Validate the entire configuration and return issues."""
        issues = []
        try:
            for section, options in self.defaults.items():
                if not self.config.has_section(section):
                    issues.append(f"Missing section: {section}")
                    continue
                    
                for key, default_value in options.items():
                    if not self.config.has_option(section, key):
                        issues.append(f"Missing option: {section}.{key}")
                        continue
                    
                    # Validate specific values
                    current_value = self.config.get(section, key)
                    try:
                        validated = self._validate_setting_value(section, key, current_value)
                        if str(validated) != current_value:
                            issues.append(f"Invalid value for {section}.{key}: {current_value} (corrected to {validated})")
                    except Exception as e:
                        issues.append(f"Validation error for {section}.{key}: {e}")
                        
        except Exception as e:
            issues.append(f"Error during validation: {e}")
            
        return issues