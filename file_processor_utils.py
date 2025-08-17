# file_processor_utils.py
import os
from constants import LANGUAGE_MAP

# --- Custom Exceptions ---
class FileProcessingError(Exception):
    """Base class for file processing errors."""
    pass

class FileTooLargeError(FileProcessingError):
    """Raised when a file is too large to process."""
    pass

class BinaryFileError(FileProcessingError):
    """Raised when a file is identified as binary."""
    pass

# --- Helper Functions ---
def get_all_files(directory):
    """Recursively gets all file paths in a directory."""
    all_files = []
    for root, _, files in os.walk(directory):
        for name in files:
            all_files.append(os.path.join(root, name))
    return all_files

def _is_binary_file(filepath, chunk_size=1024):
    """Heuristically check if a file is binary by looking for null bytes."""
    try:
        with open(filepath, 'rb') as f:
            return b'\0' in f.read(chunk_size)
    except (IOError, PermissionError):
        return True

def get_language_identifier(file_path):
    """Gets the language identifier for a file path."""
    filename = os.path.basename(file_path)
    _, ext = os.path.splitext(filename)
    if filename.lower() in LANGUAGE_MAP:
        return LANGUAGE_MAP[filename.lower()]
    if ext.lower() in LANGUAGE_MAP:
        return LANGUAGE_MAP[ext.lower()]
    return 'text'