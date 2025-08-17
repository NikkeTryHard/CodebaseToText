# caching.py
import os

class FileDetailCache:
    """
    An in-memory cache to store file details like modification time,
    line count, and content to avoid redundant I/O operations.
    """
    def __init__(self):
        self._cache = {}

    def get(self, file_path):
        """
        Retrieves an item from the cache if it exists and is not stale.
        """
        norm_path = os.path.normcase(os.path.abspath(file_path))
        if norm_path in self._cache:
            cached_data = self._cache[norm_path]
            try:
                # Invalidate cache if file modification time has changed
                if os.path.getmtime(norm_path) == cached_data.get('mtime'):
                    return cached_data
            except FileNotFoundError:
                # If file was deleted, remove it from cache
                del self._cache[norm_path]
                return None
        return None

    def set(self, file_path, data):
        """
        Adds or updates an item in the cache.
        """
        norm_path = os.path.normcase(os.path.abspath(file_path))
        try:
            # Store current modification time for future validation
            data['mtime'] = os.path.getmtime(norm_path)
            self._cache[norm_path] = data
        except FileNotFoundError:
            # Don't cache a file that doesn't exist
            pass

    def clear(self):
        """Clears the entire cache."""
        self._cache.clear()