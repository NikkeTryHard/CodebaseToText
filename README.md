# Folder to LLM-Ready Text

This is a desktop application that scans a directory and compiles the structure and contents of selected files into a single, markdown-formatted text file. This output is ideal for pasting into Large Language Model (LLM) prompts to provide context about a codebase.

## Features

- Interactive file/folder tree view for selecting what to include.
- Drag-and-drop a folder to start.
- Generates an annotated directory tree.
- Combines file contents with markdown code blocks, guessing the language for syntax highlighting.
- Handles large folders and avoids freezing the UI by processing in a background thread.
- Saves window size and last used folder between sessions.
- Customizable list of files/folders to ignore (e.g., `.git`, `node_modules`).

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
