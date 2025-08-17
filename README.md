# Folder to LLM-Ready Text

This is a desktop application that scans a directory and compiles the structure and contents of selected files into a single, markdown-formatted text file. This output is ideal for pasting into Large Language Model (LLM) prompts to provide context about a codebase.

## Features

- Interactive file/folder tree view for selecting what to include.
- Drag-and-drop a folder to start.
- Multi-threaded scanning and processing for improved speed.
- In-memory caching to accelerate repeated operations within a session.
- Generates an annotated directory tree with file line counts.
- Combines file contents with markdown code blocks, guessing the language for syntax highlighting.
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

## Future Improvements

While the current version is functional, here are some areas planned for future updates:

- **Persistent Caching:** The current cache is cleared when the application is closed. A future goal is to implement a persistent cache on disk (e.g., in a dedicated cache folder or using temporary files). This would dramatically speed up loading a previously scanned project.
- **Further Performance Tuning:** Explore more optimizations for the tree-building algorithm and UI rendering to make the application even faster on massive codebases.
- **In-App Configuration:** Add a settings window to manage the ignore list and other preferences directly within the application, removing the need to manually edit the `config.ini` file.
