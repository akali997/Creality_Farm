# Contributing Guide

Thank you for your interest in contributing to Creality Farm Manager! 🎉

## How to Contribute

### 🐛 Bug Reports

If you find a bug, please create an issue with:

- **Clear description**: What happened?
- **Steps to reproduce**: How can we recreate the issue?
- **Expected behavior**: What should happen?
- **System information**:
  - Operating System (Windows version)
  - Python version
  - Application version
  - Printer model (K1, K1 Max, etc.)
- **Logs/Screenshots**: If available

### 💡 Feature Requests

Have a great idea? Create an issue with:

- **Feature description**: What do you want?
- **Motivation**: Why is this useful?
- **Use case**: When would you use it?
- **Mockups/Examples**: If available

### 🔧 Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/akali997/Creality_Farm.git
   cd Creality_Farm
   ```

2. **Create a new branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Make your changes**
   - Write clear, understandable code
   - Add comments when necessary
   - Follow existing coding style

5. **Test your changes**
   - Run the application and test thoroughly
   - Ensure no existing features are broken
   - Test with multiple printer models if possible

6. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: brief description of changes"
   ```

   **Commit message format:**
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation updates
   - `style:` - Code formatting (no logic changes)
   - `refactor:` - Code refactoring
   - `test:` - Adding tests
   - `chore:` - Build tools, dependencies updates

7. **Push to GitHub**
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Create Pull Request**
   - Go to GitHub and create a Pull Request
   - Describe your changes clearly
   - Link related issues (if any)

## Coding Guidelines

### Python Style

- Follow PEP 8
- Use meaningful variable names
- Add docstrings for functions/classes
- Keep functions focused and concise

```python
def upload_file_to_printer(printer_ip: str, file_path: str) -> bool:
    """
    Upload G-code file to printer via Moonraker API.
    
    Args:
        printer_ip: IP address of the printer
        file_path: Local path to G-code file
        
    Returns:
        bool: True if upload successful, False otherwise
    """
    # Implementation
    pass
```

### UI/UX

- Keep UI simple and user-friendly
- Add tooltips for buttons/features
- Show progress for long operations
- Error messages should be clear and helpful

### Error Handling

```python
try:
    # Your code
    result = some_operation()
except SpecificException as e:
    logger.error(f"Failed to do something: {e}")
    # Show user-friendly error message
    show_error_dialog("Operation failed. Please try again.")
    return False
```

## Project Structure

```
Creality_Farm/
├── main.py                    # Entry point
├── ui/                        # UI components
│   └── printer_manager_app.py # Main application window
├── printer/                   # Printer operations
│   ├── api.py                # Moonraker API wrapper
│   ├── discovery.py          # Network scanning
│   └── file_manager.py       # File operations
├── threads/                   # Worker threads
│   ├── upload_thread.py      # Upload operations
│   └── ...
├── config/                    # Configuration
│   └── settings.py           # App settings
└── IP/                        # IP management tools
```

## Review Process

1. Maintainers will review your code
2. There may be feedback/requests for changes
3. Make changes if needed
4. Once approved, PR will be merged

## Questions?

- Open an issue with `question` label
- Or start a discussion on GitHub

## Code of Conduct

- Be respectful to each other
- Provide constructive feedback
- Accept different opinions
- Focus on building the best tool possible

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for helping make Creality Farm Manager better! 🚀**
