# CodebaseToText

This desktop application scans a directory and compiles the structure and contents of selected files into a single, markdown-formatted text file. This output is ideal for pasting into Large Language Model (LLM) prompts to provide context about a codebase.

## Features

- **Blazing Fast Generation:** An optimized architecture reads all file data during the initial scan, making the final text generation instantaneous.
- **Interactive Tree View:** Easily check or uncheck files and folders to include in the output.
- **In-App Ignore List Editor:** A new preferences window allows you to easily manage the list of ignored files and folders (e.g., `.git`, `node_modules`) without manually editing config files.
- **Multi-threaded Scanning:** The initial directory scan is multi-threaded for a significant speed boost on large codebases.
- **Drag-and-Drop:** Simply drop a folder onto the application window to start scanning.
- **Smart Formatting:** Generates an annotated directory tree with file line counts and combines file contents into markdown code blocks, automatically detecting the language for syntax highlighting.
- **Session Persistence:** Remembers window size and the last used folder between sessions.

## Installation

1.  Ensure you have Python 3 installed.
2.  Clone this repository or download the source code.
3.  Install the required dependency using pip:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the application from the command line:

```bash
python main.py
```

For more detailed logging in the terminal, use the verbose flag:

```bash
python main.py -v
```

## Future Improvements & TODO

Here are some planned features and ideas for future versions:

- **Treeview Search/Filter:** Add a search bar above the treeview to filter files and folders by name. This would be extremely useful for navigating large codebases.

  - _Implementation Idea: Bind to the `<KeyRelease>` event on an Entry widget, then recursively traverse the tree to hide non-matching items._

- **Theme Toggle:** Add a menu item to switch between light and dark themes on-the-fly and save the preference to the config file.

  - _Implementation Idea: The `azure.tcl` theme engine already supports this; just need to call the `set_theme` procedure and update the config._

- **Direct Export Options:** Add buttons in the output window to save the generated text directly to a file (`.md`, `.txt`) or to copy the content automatically.

  - _Implementation Idea: Could also explore exporting as a `.zip` archive containing the original selected files._

- **File Preview:** Implement a feature to double-click a file in the treeview to open a small, read-only preview window showing its content. This would help users decide what to include without leaving the application.

- **Total Stats Display:** Show useful statistics in the status bar after a scan is complete, such as "X files selected, Y total lines of code".

  - _Implementation Idea: Could also estimate the final output size in characters or tokens during generation._

- **Ignore Patterns with Wildcards:** Enhance the ignore list to support glob patterns (e.g., `*.pyc`, `*.log`) in addition to exact names.

  - _Implementation Idea: Use Python's `fnmatch` library for pattern matching against file and directory names._

- **LLM Prompt Templates:** Add a dropdown menu near the "Generate" button with pre-built prompt starters (e.g., "Analyze this codebase for potential bugs:", "Refactor the following code for better readability:") that get prepended to the final output.
