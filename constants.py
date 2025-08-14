# constants.py

# --- UI Constants ---
CHECKED_EMOJI = "✅"
UNCHECKED_EMOJI = "⬜️"

# --- Processing Constants ---
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# --- Default Ignored Items ---
# This set contains common directories and files to ignore during processing.
# It can be extended via the config.ini file.
DEFAULT_IGNORED_ITEMS = {
    '__pycache__', '.git', '.vscode', 'node_modules', '.idea', '.DS_Store',
    'build', 'dist', '.env'
}


# --- File Type Mapping for Syntax Highlighting ---
LANGUAGE_MAP = {
    '.py': 'python', '.pyw': 'python',
    '.js': 'javascript', '.mjs': 'javascript',
    '.ts': 'typescript', '.tsx': 'typescript',
    '.html': 'html', '.htm': 'html',
    '.css': 'css', '.scss': 'scss', '.sass': 'sass',
    '.json': 'json', '.jsonc': 'json',
    '.xml': 'xml',
    '.md': 'markdown', '.markdown': 'markdown',
    '.sh': 'shell', '.bash': 'shell',
    '.bat': 'batch',
    '.java': 'java',
    '.c': 'c', '.h': 'c',
    '.cpp': 'cpp', '.hpp': 'cpp', '.cxx': 'cpp',
    '.cs': 'csharp',
    '.go': 'go',
    '.php': 'php',
    '.rb': 'ruby',
    '.rs': 'rust',
    '.swift': 'swift',
    '.kt': 'kotlin', '.kts': 'kotlin',
    '.sql': 'sql',
    '.yaml': 'yaml', '.yml': 'yaml',
    '.dockerfile': 'dockerfile',
    '.toml': 'toml',
    '.ini': 'ini',
    '.txt': 'text',
    '.r': 'r',
    '.pl': 'perl',
    '.vba': 'vba',
    '.lua': 'lua',
    '.ps1': 'powershell',
    '.dart': 'dart',
    '.ex': 'elixir', '.exs': 'elixir',
    '.erl': 'erlang',
    '.fs': 'fsharp',
    '.hs': 'haskell',
    '.jl': 'julia',
    '.lisp': 'lisp',
    '.pas': 'pascal',
    '.rkt': 'racket',
    '.sc': 'scala',
    '.scm': 'scheme',
    '.vb': 'vbnet',
}