# CodebaseToText v7.4 - Enhanced Edition

🎯 **Convert your codebase to LLM-ready markdown with enhanced UI and better user experience**

## ✨ What's New in v7.4

### 🎨 Enhanced User Interface

- **Modern Design**: Clean, intuitive interface with better spacing and typography
- **Visual Feedback**: Hover effects, animations, and status indicators
- **Icons & Emojis**: Visual elements for better user understanding
- **Responsive Layout**: Better window sizing and component arrangement

### 🚀 Improved User Experience

- **Drag & Drop**: Enhanced folder selection with visual feedback
- **Keyboard Shortcuts**: Ctrl+O (open), Ctrl+S (settings), Ctrl+Q (quit), F5 (refresh)
- **Context Menus**: Right-click support for tree items
- **Progress Tracking**: Real-time progress bars and status updates
- **Smart Validation**: Better error messages and user guidance

### 🛡️ Enhanced Error Handling & Robustness

- **Comprehensive Error Handling**: Graceful handling of file system errors
- **User-Friendly Messages**: Clear, actionable error messages
- **Fallback Mechanisms**: Automatic recovery from common issues
- **Debug Mode**: Enhanced logging for troubleshooting

### ⚡ Performance Improvements

- **Optimized Scanning**: Faster directory processing
- **Memory Management**: Better handling of large codebases
- **Threading**: Improved background operations
- **Caching**: Smart caching for repeated operations

### 🔧 Advanced Configuration

- **Enhanced Settings**: More configuration options
- **Theme Support**: Dark/Light theme switching
- **Customizable Ignore Lists**: Smart pattern matching
- **Export/Import**: Configuration backup and sharing

## 🚀 Features

### Core Functionality

- **Directory Scanning**: Fast, intelligent codebase analysis
- **File Filtering**: Smart ignore patterns and file type detection
- **Markdown Generation**: LLM-optimized output format
- **Progress Tracking**: Real-time operation status

### Enhanced UI Elements

- **Tree View**: Interactive file/folder selection with checkboxes
- **Status Bar**: Real-time operation feedback
- **Progress Bars**: Visual progress indication
- **Tooltips**: Helpful information on hover

### Advanced Options

- **File Size Limits**: Configurable maximum file sizes
- **Threading Control**: Adjustable thread counts
- **Caching Options**: Performance optimization settings
- **Verbose Logging**: Detailed operation logging

## 🎯 Use Cases

- **AI/LLM Development**: Prepare codebases for AI analysis
- **Documentation**: Generate comprehensive code documentation
- **Code Review**: Share code with team members
- **Learning**: Study codebases in a readable format
- **Archiving**: Create searchable code archives

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- Windows, macOS, or Linux

### Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd CodebaseToText

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Command Line Options

```bash
python main.py --help
python main.py -v                    # Verbose mode
python main.py --debug               # Debug mode
python main.py --config custom.ini   # Custom config file
```

## 📖 Usage

### Basic Workflow

1. **Select Folder**: Choose your codebase root directory
2. **Review Files**: Browse and select files to include
3. **Generate Output**: Create LLM-ready markdown
4. **Copy/Save**: Use the output as needed

### Advanced Features

- **Drag & Drop**: Drop folders directly onto the application
- **Keyboard Navigation**: Use arrow keys and spacebar in tree view
- **Context Menus**: Right-click for additional options
- **Settings**: Customize behavior in Preferences

### Keyboard Shortcuts

- `Ctrl+O`: Open folder dialog
- `Ctrl+S`: Open settings
- `Ctrl+Q`: Quit application
- `F5`: Refresh tree view
- `Space`: Toggle file selection
- `Enter`: Open file or expand folder

## ⚙️ Configuration

### Settings File

The application creates a `config.ini` file with your preferences:

```ini
[Settings]
width = 900
height = 800
theme = dark
max_file_size = 10
auto_save = True
verbose = False

[Advanced]
scan_timeout = 300
max_threads = 4
chunk_size = 50000
```

### Ignore Patterns

Customize which files to ignore:

```
# Build directories
node_modules/
build/
dist/

# Cache files
*.log
*.tmp
*.cache

# OS files
.DS_Store
Thumbs.db
```

## 🔧 Troubleshooting

### Common Issues

- **Large Files**: Adjust `max_file_size` in settings
- **Slow Performance**: Reduce `max_threads` or disable animations
- **Memory Issues**: Increase `chunk_size` for better memory management

### Debug Mode

Run with `--debug` flag for detailed logging:

```bash
python main.py --debug
```

### Error Reporting

- Check console output for error details
- Enable verbose mode with `-v` flag
- Review log files in debug mode

## 🚀 Performance Tips

- **Use Ignore Lists**: Exclude unnecessary files and directories
- **Adjust Thread Count**: Optimize for your system
- **Enable Caching**: Improve repeated operations
- **Disable Animations**: Better performance on slower systems

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for details.

### Development Setup

```bash
# Clone and setup
git clone <repository-url>
cd CodebaseToText
pip install -r requirements.txt

# Run in development mode
python main.py --debug
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **TkinterDnD2**: Drag and drop functionality
- **Azure Theme**: Modern UI styling
- **Python Community**: Excellent libraries and tools

## 📞 Support

- **Issues**: Report bugs and request features
- **Documentation**: Check this README and inline code comments
- **Community**: Join our discussions and share feedback

---

**Made with ❤️ for the AI/LLM development community**

_Transform your codebases into AI-ready formats with ease and style!_
